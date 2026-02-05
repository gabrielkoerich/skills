# Common Mistakes in Solana Smart Contract Implementation

31 vulnerability patterns from real-world Solana programs, plus 4 case studies from production incidents.

Sources: [SlowMist Security Best Practices](https://github.com/slowmist/solana-smart-contract-security-best-practices), [Zealynx Security Checklist](https://www.zealynx.io/blogs/solana-security-checklist), [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security)

## Index

### Arithmetic (1-4)
- [1. Integer Overflow or Underflow](#1-integer-overflow-or-underflow)
- [2. Loss of Precision](#2-loss-of-precision)
- [3. Inaccurate Calculation with Saturating Arithmetic](#3-inaccurate-calculation-with-saturating-arithmetic)
- [4. Panic Due to Division by Zero](#4-panic-due-to-division-by-zero)

### Error Handling (5)
- [5. Error Not Handled](#5-error-not-handled)

### Account Validation (6-12)
- [6. Missing Permission Check on Caller](#6-missing-permission-check-on-caller)
- [7. Account Signer Check Missing](#7-account-signer-check-missing)
- [8. Account Writable Check Missing](#8-account-writable-check-missing)
- [9. Account Owner / Program ID Check Missing](#9-account-owner--program-id-check-missing)
- [10. Account Initialized Check Missing](#10-account-initialized-check-missing)
- [11. PDA Substitution](#11-pda-substitution)
- [12. Missing System Account Check](#12-missing-system-account-check)

### State Management (13-15)
- [13. Missing Check for Lamports](#13-missing-check-for-lamports)
- [14. Pyth Oracle Status Check](#14-pyth-oracle-status-check)
- [15. Missing State Reset on Ownership Change](#15-missing-state-reset-on-ownership-change)

### Anchor-Specific (16)
- [16. Account Reloading After CPI](#account-reloading-after-cpi)

### Additional Security Patterns (17-26)
- [17. Casting Vulnerabilities](#17-casting-vulnerabilities)
- [18. Authority Transfer Pitfalls](#18-authority-transfer-pitfalls)
- [19. Account Data Reallocation](#19-account-data-reallocation)
- [20. CPI Signer Pitfalls](#20-cpi-signer-pitfalls)
- [21. Security Dependency Chain](#21-security-dependency-chain)
- [22. Frontrunning / Missing Slippage Protection](#22-frontrunning--missing-slippage-protection)
- [23. Remaining Accounts Validation](#23-remaining-accounts-validation)
- [24. Unsafe Rust](#24-unsafe-rust)
- [25. Vector Length Bug](#25-vector-length-bug)
- [26. Seed Collisions](#26-seed-collisions)

### Advanced Issues (27-31)
- [27. Dangling Pointers](#27-dangling-pointers)
- [28. Account Reassignment Bug](#28-account-reassignment-bug)
- [29. Heap Exhaustion](#29-heap-exhaustion)
- [30. Account Constraint Fragility](#30-account-constraint-fragility)
- [31. Ed25519 Introspection](#31-ed25519-introspection)

### Case Studies
- [Case 1: Wormhole Bridge Hack](#case-1-wormhole-bridge-hack----sysvar-not-checked)
- [Case 2: Jet Protocol -- PDA Without Caller Validation](#case-2-pda-account-without-callerbeneficiary-validation)
- [Case 3: Mango Markets -- Price Manipulation](#case-3-mango-markets----price-manipulation)
- [Case 4: Cashio -- Missing Account Validation](#case-4-cashio----missing-account-validation)

---

## Arithmetic Mistakes

### 1. Integer Overflow or Underflow

**Severity**: High

Calculating without checking for overflow/underflow. Rust wraps silently in release builds.

```rust
// VULNERABLE
pub fn handler(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    let user_balance = ctx.accounts.user.balance + amount; // Wraps on overflow!
}
```

**Fix**: Use `checked_add` / `checked_sub` / `checked_mul` / `checked_div`:
```rust
let user_balance = ctx.accounts.user.balance
    .checked_add(amount)
    .ok_or(ErrorCode::Overflow)?;
```

### 2. Loss of Precision

**Severity**: High

Using `try_round_u64()` for rounding leads to precision problems that enable arbitrage attacks.

```rust
// VULNERABLE
pub fn collateral_to_liquidity(&self, collateral_amount: u64) -> Result<u64, ProgramError> {
    Decimal::from(collateral_amount)
        .try_div(self.0)?
        .try_round_u64() // Rounds up -- attacker exploits rounding direction
}
```

**Fix**: Use `try_floor_u64()` to prevent arbitrage:
```rust
Decimal::from(collateral_amount)
    .try_div(self.0)?
    .try_floor_u64() // Always rounds down -- safe
```

### 3. Inaccurate Calculation with Saturating Arithmetic

**Severity**: High

`saturating_add` / `saturating_sub` / `saturating_mul` clamp to min/max instead of failing, producing silently wrong results.

```rust
// VULNERABLE -- saturating_sub returns 0 instead of failing when overpaying
let over_fee = paid_amount.saturating_sub(actual_amount);
```

**Fix**: Use `checked_*()` methods that return `None` on invalid operations:
```rust
let over_fee = paid_amount
    .checked_sub(actual_amount)
    .ok_or(ErrorCode::InsufficientPayment)?;
```

### 4. Panic Due to Division by Zero

**Severity**: High

Division by zero panics and terminates the program.

```rust
// VULNERABLE
let result = dividend / divisor; // Panics if divisor == 0!
```

**Fix**: Check before dividing, or use `checked_div`:
```rust
let result = dividend
    .checked_div(divisor)
    .ok_or(ErrorCode::DivisionByZero)?;
```

---

## Error Handling Mistakes

### 5. Error Not Handled

**Severity**: High

Calling functions that return `Result` without handling the error (missing `?`).

```rust
// VULNERABLE -- Result ignored, transfer may have failed silently
&spl_token::instruction::transfer(
    //...
);
```

**Fix**: Always propagate errors with `?`:
```rust
spl_token::instruction::transfer(
    //...
)?; // Propagates any error
```

---

## Account Validation Mistakes

### 6. Missing Permission Check on Caller

**Severity**: Low

Not checking if the signer is a legitimate administrator when initializing global config accounts. Anyone can create a fake global state.

```rust
// VULNERABLE -- anyone can call init_market
fn init_market(accounts: &[AccountInfo]) -> ProgramResult {
    Ok(()) // No admin check!
}
```

**Fix**: Hardcode admin key or use a PDA with admin seeds:
```rust
const ADMIN: Pubkey = pubkey!("AdminPubkeyHere...");

fn init_market(accounts: &[AccountInfo]) -> ProgramResult {
    let signer = &accounts[0];
    require!(signer.key == &ADMIN, ErrorCode::Unauthorized);
    Ok(())
}
```

### 7. Account Signer Check Missing

**Severity**: High

Not verifying that the expected signer actually signed the transaction.

**Fix** (native):
```rust
let payer_account = next_account_info(accounts_iter)?;
if !payer_account.is_signer {
    return Err(ProgramError::MissingRequiredSignature);
}
```

**Fix** (Anchor): Use `Signer<'info>` type.

### 8. Account Writable Check Missing

**Severity**: High

Not verifying that a state account is marked as writable before modifying it.

**Fix** (native):
```rust
let hello_state_account = next_account_info(accounts_iter)?;
if !hello_state_account.is_writable {
    return Err(ProgramError::InvalidAccountData);
}
```

**Fix** (Anchor): Use `#[account(mut)]` constraint.

### 9. Account Owner / Program ID Check Missing

**Severity**: High

Reading account data without verifying the account is owned by the expected program. Attacker creates a fake account with crafted data.

```rust
// VULNERABLE -- pyth_price_info could be owned by an attacker's program
let pyth_price_info = next_account_info(account_info_iter)?;
let market_price = get_pyth_price(pyth_price_info, clock)?;
```

**Fix**: Verify owner before reading:
```rust
let program_id = Pubkey::from_str("FsJ3A3u2vn5cTVofAjvy6y5kwABJAqYWpe4975bi2epH").unwrap();
if pyth_price_info.owner.ne(&program_id) {
    return Err(ProgramError::IllegalOwner);
}
```

### 10. Account Initialized Check Missing

**Severity**: High

Not checking if an account has already been initialized, allowing re-initialization attacks.

**Fix** (native):
```rust
let mut hello_state = HelloState::try_from_slice(&hello_state_account.data.borrow())?;
if hello_state.is_initialized {
    return Err(ProgramError::AccountAlreadyInitialized);
}
hello_state.is_initialized = true;
hello_state.serialize(&mut &mut hello_state_account.data.borrow_mut()[..])?;
```

**Fix** (Anchor): Use `#[account(init, ...)]` -- fails if account already exists.

### 11. PDA Substitution

**Severity**: High

Using an unchecked account as a PDA seed input, allowing attacker to substitute a different base account and derive a different PDA.

```rust
// VULNERABLE -- config_pda_info can be replaced by an unofficial account
let config_pda_info = next_account_info(account_info_iter)?;
let seeds = &[b"user_pda_desc".as_ref(), config_pda_info.key.as_ref(), &[bump]];
let user_pda_pubkey = Pubkey::create_program_address(seeds, program_id)?;
```

**Fix**: Derive PDAs from unique, verified accounts (e.g., program-owned config accounts).

### 12. Missing System Account Check

**Severity**: High

Not verifying system/sysvar accounts before use. Attacker passes a fake token program or sysvar.

```rust
// VULNERABLE -- token_program_id not validated
let token_program_id = next_account_info(account_info_iter)?;
spl_token_transfer(TokenTransferParams {
    token_program: token_program_id.clone(),
})?;
```

**Fix**: Hardcode expected addresses and validate:
```rust
if *token_program_id.key != spl_token::ID {
    return Err(ProgramError::IncorrectProgramId);
}
```

Or in Anchor: `Program<'info, Token>`.

---

## State Management Mistakes

### 13. Missing Check for Lamports

**Severity**: Low

When an account is "deleted" (lamports set to zero), the data can still be read within the same transaction. Reading without checking lamports leads to stale data access.

**Fix**: Check lamports before reading:
```rust
if **the_account_to_read.try_borrow_lamports()? > 0 {
    // Safe to read account data
}
```

### 14. Pyth Oracle Status Check

**Severity**: High

Not checking Pyth oracle price feed status before using the price. Oracle may be stale or in error state.

```rust
// Must check status before using price
if pyth_price.agg.status != PriceStatus::Trading {
    return Err(ErrorCode::InvalidPythConfig);
}
```

**Fix**: Upgrade to the latest Pyth SDK and always check `PriceStatus::Trading`.

### 15. Missing State Reset on Ownership Change

**Severity**: High

When changing account owner, delegated permissions and amounts are not reset, leaving stale authorizations.

```rust
// VULNERABLE
if let COption::Some(authority) = new_authority {
    account.owner = authority;
}
// delegate and delegated_amount are still set to old values!
```

**Fix**: Reset all delegated state when changing ownership:
```rust
if let COption::Some(authority) = new_authority {
    account.owner = authority;
}
account.delegate = COption::None;
account.delegated_amount = 0;
if account.is_native() {
    account.close_authority = COption::None;
}
```

---

## Anchor-Specific Mistake

### Account Reloading After CPI

**Severity**: High

After a CPI, Anchor's deserialized account data is stale. Reading fields without calling `.reload()` returns pre-CPI values.

```rust
// VULNERABLE
anchor_spl::token::mint_to(cpi_ctx, amount)?;
msg!("Supply: {}", ctx.accounts.mint.supply); // STALE! Shows pre-mint value
```

**Fix**: Call `.reload()` after any CPI that modifies an account you'll read:
```rust
anchor_spl::token::mint_to(cpi_ctx, amount)?;
ctx.accounts.mint.reload()?; // Refresh from on-chain data
msg!("Supply: {}", ctx.accounts.mint.supply); // Correct post-mint value
```

---

## Additional Security Patterns

### 17. Casting Vulnerabilities

**Severity**: High

Using `as` for integer casts silently truncates or wraps values. This is especially dangerous when casting user input or calculated values.

```rust
// VULNERABLE -- silent truncation
let amount_u32 = amount_u64 as u32;    // Truncates high bits!
let positive = negative_i64 as u64;     // Wraps to huge number!
let small = big_u128 as u64;            // Truncates!
```

**Fix**: Use `try_from` for narrowing conversions, `from` for widening:
```rust
// Safe narrowing (may fail)
let amount_u32 = u32::try_from(amount_u64)
    .map_err(|_| ErrorCode::CastOverflow)?;

// Safe sign check before cast
require!(value_i64 >= 0, ErrorCode::NegativeValue);
let positive = u64::try_from(value_i64)
    .map_err(|_| ErrorCode::CastOverflow)?;

// Safe widening (always succeeds)
let big = u128::from(amount_u64);
```

**Key rule**: Never use `as` for narrowing casts on user-provided or calculated values. Always use `try_from()`.

### 18. Authority Transfer Pitfalls

**Severity**: High

Single-step authority transfers are dangerous: if the new authority key is wrong, the program is permanently locked.

```rust
// VULNERABLE -- single-step transfer, no recovery possible
pub fn transfer_authority(ctx: Context<TransferAuth>, new_authority: Pubkey) -> Result<()> {
    ctx.accounts.config.authority = new_authority; // If wrong key, game over!
    Ok(())
}
```

**Fix**: Implement two-step nominate/accept pattern:
```rust
pub fn nominate_authority(ctx: Context<NominateAuth>, nominee: Pubkey) -> Result<()> {
    require!(nominee != Pubkey::default(), ErrorCode::InvalidAuthority);
    ctx.accounts.config.pending_authority = Some(nominee);
    Ok(())
}

pub fn accept_authority(ctx: Context<AcceptAuth>) -> Result<()> {
    let config = &mut ctx.accounts.config;
    require!(
        config.pending_authority == Some(ctx.accounts.new_authority.key()),
        ErrorCode::NotNominated
    );
    config.authority = ctx.accounts.new_authority.key();
    config.pending_authority = None;
    Ok(())
}

// Allow current authority to cancel a pending nomination
pub fn cancel_nomination(ctx: Context<CancelNomination>) -> Result<()> {
    ctx.accounts.config.pending_authority = None;
    Ok(())
}
```

**Checklist**:
- [ ] Two-step transfer: nominate, then accept
- [ ] Validate new authority is not `Pubkey::default()`
- [ ] Allow current authority to cancel nomination
- [ ] Both steps require appropriate signer checks

### 19. Account Data Reallocation

**Severity**: Medium

Improper use of `realloc` with the `zero_init` parameter can expose stale data or waste compute.

```rust
// VULNERABLE -- zero_init=false after shrink+grow exposes old data
#[account(
    mut,
    realloc = new_size,
    realloc::payer = payer,
    realloc::zero_init = false, // If account was shrunk then grown, old data leaks!
)]
pub data_account: Account<'info, DynamicData>,
```

**Fix**: Set `zero_init = true` when account size may have decreased before increasing:
```rust
#[account(
    mut,
    realloc = new_size,
    realloc::payer = payer,
    realloc::zero_init = true, // Zeros new space -- safe but costs more CU
)]
pub data_account: Account<'info, DynamicData>,
```

**Best practices**:
- [ ] Use `zero_init = true` when size increases after a prior decrease
- [ ] Bound dynamic data sizes with constants
- [ ] Consider fixed-size accounts to avoid realloc entirely
- [ ] Use Address Lookup Tables (ALTs) instead when managing dynamic account sets

### 20. CPI Signer Pitfalls

**Severity**: Critical

Forwarding user wallets as signers to third-party CPIs allows malicious programs to drain the user's funds.

```rust
// VULNERABLE -- user wallet forwarded to arbitrary CPI
pub fn interact_with_protocol(ctx: Context<Interact>) -> Result<()> {
    let cpi_ctx = CpiContext::new(
        ctx.accounts.external_program.to_account_info(),
        ExternalInstruction {
            user_wallet: ctx.accounts.user.to_account_info(), // User's signer forwarded!
            // The external program now has signing authority over user's wallet
        },
    );
    external_program::do_something(cpi_ctx)?;
    Ok(())
}
```

**Fix**: Use protocol-owned PDAs as CPI authorities instead:
```rust
pub fn interact_with_protocol(ctx: Context<Interact>) -> Result<()> {
    // Use a protocol PDA as the authority, not the user's wallet
    let seeds = &[b"protocol_authority", &[ctx.accounts.config.auth_bump]];
    let signer_seeds = &[&seeds[..]];

    let cpi_ctx = CpiContext::new_with_signer(
        ctx.accounts.external_program.to_account_info(),
        ExternalInstruction {
            authority: ctx.accounts.protocol_pda.to_account_info(),
        },
        signer_seeds,
    );
    external_program::do_something(cpi_ctx)?;

    // Verify state after CPI
    ctx.accounts.vault.reload()?;
    require!(
        **ctx.accounts.vault.to_account_info().try_borrow_lamports()? >= expected_balance,
        ErrorCode::UnexpectedBalanceChange
    );
    Ok(())
}
```

**Key rule**: Never forward user wallets as signers to third-party CPIs. Use protocol PDAs as intermediary authorities. Check balances before/after CPI.

### 21. Security Dependency Chain

**Severity**: High

When validation of one account depends on another account, and that root account is unconstrained, the entire validation chain is broken.

```rust
// VULNERABLE -- config is unconstrained, so all downstream checks are meaningless
#[derive(Accounts)]
pub struct Withdraw<'info> {
    pub config: Account<'info, Config>,          // UNCONSTRAINED! Attacker provides fake config
    #[account(
        constraint = vault.config == config.key() // Meaningless -- config is fake
    )]
    pub vault: Account<'info, Vault>,
    #[account(
        constraint = user_state.vault == vault.key() // Also meaningless
    )]
    pub user_state: Account<'info, UserState>,
}
```

**Fix**: Anchor every dependency chain to a verified root (PDA or hardcoded key):
```rust
#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(
        seeds = [b"config"],
        bump = config.bump, // PDA -- cannot be faked
    )]
    pub config: Account<'info, Config>,
    #[account(
        constraint = vault.config == config.key() @ ErrorCode::InvalidVault
    )]
    pub vault: Account<'info, Vault>,
    #[account(
        constraint = user_state.vault == vault.key() @ ErrorCode::InvalidUserState,
        constraint = user_state.owner == user.key() @ ErrorCode::Unauthorized,
    )]
    pub user_state: Account<'info, UserState>,
    pub user: Signer<'info>,
}
```

**Key rule**: Every validation chain must start from a verified root account (PDA or hardcoded). One unconstrained account poisons all downstream constraints.

### 22. Frontrunning / Missing Slippage Protection

**Severity**: High

Without expected-value checks, attackers can manipulate state between transaction submission and execution (sandwich attacks, MEV).

```rust
// VULNERABLE -- no slippage protection
pub fn swap(ctx: Context<Swap>, amount_in: u64) -> Result<()> {
    let amount_out = calculate_output(amount_in, &ctx.accounts.pool)?;
    // Attacker can manipulate pool price between user's tx submission and execution
    transfer_to_user(ctx, amount_out)?;
    Ok(())
}
```

**Fix**: Require expected values and deadlines:
```rust
pub fn swap(
    ctx: Context<Swap>,
    amount_in: u64,
    minimum_amount_out: u64,    // Slippage protection
    deadline: i64,               // Transaction expiry
) -> Result<()> {
    let clock = Clock::get()?;
    require!(clock.unix_timestamp <= deadline, ErrorCode::TransactionExpired);

    let amount_out = calculate_output(amount_in, &ctx.accounts.pool)?;
    require!(amount_out >= minimum_amount_out, ErrorCode::SlippageExceeded);

    transfer_to_user(ctx, amount_out)?;
    Ok(())
}
```

**Checklist**:
- [ ] All swaps/trades include `minimum_amount_out` parameter
- [ ] Include transaction `deadline` parameter
- [ ] For sensitive operations, consider commit-reveal patterns
- [ ] Validate expected state values in instruction parameters

### 23. Remaining Accounts Validation

**Severity**: Medium

`ctx.remaining_accounts` bypasses all Anchor validation. Accounts passed here have no automatic ownership, type, or signer checks.

```rust
// VULNERABLE -- remaining accounts used without validation
pub fn process_batch(ctx: Context<ProcessBatch>) -> Result<()> {
    for account in ctx.remaining_accounts.iter() {
        // No ownership check, no type check, no signer check!
        let data = account.try_borrow_data()?;
        process_account_data(&data)?;
    }
    Ok(())
}
```

**Fix**: Manually validate each remaining account:
```rust
pub fn process_batch(ctx: Context<ProcessBatch>) -> Result<()> {
    for account in ctx.remaining_accounts.iter() {
        // Validate ownership
        require!(
            account.owner == ctx.program_id,
            ErrorCode::InvalidAccountOwner
        );
        // Validate discriminator (type check)
        let data = account.try_borrow_data()?;
        require!(
            data.len() >= 8 && data[..8] == UserState::DISCRIMINATOR,
            ErrorCode::InvalidAccountType
        );
        // Validate eligibility
        let user_state = UserState::try_deserialize(&mut &data[..])?;
        require!(user_state.is_eligible, ErrorCode::NotEligible);

        process_user_state(&user_state)?;
    }
    Ok(())
}
```

**Key rule**: Treat `remaining_accounts` as fully untrusted. Validate ownership, discriminator, and data for every account. Document the expected format.

### 24. Unsafe Rust

**Severity**: High

`unsafe` blocks bypass Rust's memory safety guarantees. In Solana programs, this can lead to memory corruption, data leaks, or exploitable behavior.

```rust
// VULNERABLE -- unnecessary unsafe for performance
pub fn fast_copy(ctx: Context<FastCopy>) -> Result<()> {
    unsafe {
        let src = ctx.accounts.source.to_account_info().data.borrow();
        let dst = &mut ctx.accounts.dest.to_account_info().data.borrow_mut();
        std::ptr::copy_nonoverlapping(src.as_ptr(), dst.as_mut_ptr(), src.len());
        // Buffer overflow if dst is smaller than src!
    }
    Ok(())
}
```

**Fix**: Use safe Rust alternatives:
```rust
pub fn safe_copy(ctx: Context<SafeCopy>) -> Result<()> {
    let src = ctx.accounts.source.to_account_info().try_borrow_data()?;
    let mut dst = ctx.accounts.dest.to_account_info().try_borrow_mut_data()?;
    require!(dst.len() >= src.len(), ErrorCode::BufferTooSmall);
    dst[..src.len()].copy_from_slice(&src);
    Ok(())
}
```

**Rules**:
- [ ] Minimize `unsafe` blocks -- use safe alternatives first
- [ ] If `unsafe` is necessary, validate ALL inputs before the block
- [ ] Document WHY unsafe is needed with `// SAFETY:` comments
- [ ] Encapsulate unsafe code in safe abstractions
- [ ] Audit all `unsafe` blocks in security reviews

### 25. Vector Length Bug

**Severity**: Medium

`vec![N]` creates a vector with one element (the value N), while `vec![0; N]` creates a vector with N zeros. This is a common Rust mistake.

```rust
// VULNERABLE -- creates vec with ONE element (value 100), not 100 elements
let scores = vec![100]; // scores.len() == 1, scores[0] == 100

// Then indexing panics:
scores[50] = 42; // PANIC: index out of bounds!
```

**Fix**: Use correct vec initialization syntax:
```rust
// Correct: 100 elements, all initialized to 0
let scores = vec![0u64; 100]; // scores.len() == 100

// Or use push/extend for dynamic building
let mut scores = Vec::with_capacity(100);
for _ in 0..100 {
    scores.push(0);
}
```

**Key rule**: When creating fixed-size vectors, always use `vec![default_value; count]` syntax. Prefer `push`/`extend` for dynamic building.

### 26. Seed Collisions

**Severity**: High

PDAs with overlapping seed patterns can collide, allowing one user or feature to access another's account.

```rust
// VULNERABLE -- seeds can collide between features
// User vault: seeds = [b"vault", user.key()]
// Admin vault: seeds = [b"vault", admin.key()]
// If admin IS a user, they share the same PDA namespace!

// Worse -- variable-length seeds without separators:
// seeds = [b"pool", token_a.key(), token_b.key()]
// vs
// seeds = [b"poolt", oken_a_key_bytes..., token_b.key()]
// Could collide if seed bytes align!
```

**Fix**: Use unique prefixes and include discriminating data:
```rust
// Distinct prefixes per feature
#[account(
    seeds = [b"user_vault", user.key().as_ref()],
    bump
)]
pub user_vault: Account<'info, UserVault>,

#[account(
    seeds = [b"admin_vault", admin.key().as_ref()],
    bump
)]
pub admin_vault: Account<'info, AdminVault>,

// For pools: include both keys in canonical order
#[account(
    seeds = [
        b"pool",
        std::cmp::min(token_a.key(), token_b.key()).as_ref(),
        std::cmp::max(token_a.key(), token_b.key()).as_ref(),
    ],
    bump
)]
pub pool: Account<'info, Pool>,
```

**Key rule**: Use unique string prefixes per account type. Include all discriminating data (user pubkey, IDs, type tags) in seeds. Test for collisions across features.

---

## Advanced Issues

### 27. Dangling Pointers

**Severity**: High

Holding references to accounts that are closed by CPIs within the same transaction can lead to reading zeroed or reallocated memory.

```rust
// VULNERABLE -- reference held across CPI that closes the account
pub fn process(ctx: Context<Process>) -> Result<()> {
    let balance = ctx.accounts.source.amount; // Cache a value

    // CPI closes source account
    close_account_cpi(ctx)?;

    // balance is stale, source account data may be zeroed
    msg!("Had balance: {}", balance); // May show wrong data
    // ctx.accounts.source is now a dangling reference
    Ok(())
}
```

**Fix**: Don't hold references across CPIs that close accounts. Reload or re-fetch after CPI:
```rust
pub fn process(ctx: Context<Process>) -> Result<()> {
    // Do all reads BEFORE closing
    let balance = ctx.accounts.source.amount;
    require!(balance > 0, ErrorCode::EmptyAccount);

    // Close the account
    close_account_cpi(ctx)?;

    // Do NOT read from source after closing
    // Use the cached value if needed
    emit!(AccountClosed { final_balance: balance });
    Ok(())
}
```

### 28. Account Reassignment Bug

**Severity**: Medium

Temporarily changing an account's owner (e.g., assigning to System Program then back) can cause the runtime to zero the account data.

```rust
// VULNERABLE -- temporary owner change wipes data
pub fn process(ctx: Context<Process>) -> Result<()> {
    let account = &ctx.accounts.data_account;

    // Reassign to system program (data may be wiped!)
    account.assign(&system_program::ID);

    // Reassign back (data is gone!)
    account.assign(ctx.program_id);

    // account data is now zeroed
    Ok(())
}
```

**Fix**: Avoid temporary reassignments. If you must change ownership, save and restore data explicitly:
```rust
pub fn process(ctx: Context<Process>) -> Result<()> {
    // Save data before reassignment
    let data_backup = ctx.accounts.data_account.data.clone();

    // Perform necessary ownership change
    // ...

    // Restore data after reassignment
    let mut account_data = ctx.accounts.data_account.try_borrow_mut_data()?;
    account_data.copy_from_slice(&data_backup);
    Ok(())
}
```

### 29. Heap Exhaustion

**Severity**: Medium

Solana programs have a 32KB heap limit. Unbounded allocations cause out-of-memory panics.

```rust
// VULNERABLE -- unbounded allocation
pub fn process_all(ctx: Context<ProcessAll>) -> Result<()> {
    let count = ctx.accounts.config.item_count; // Could be huge!
    let mut items = Vec::with_capacity(count as usize); // May exceed 32KB heap!

    for i in 0..count {
        items.push(process_item(i)?); // Keeps growing
    }
    Ok(())
}
```

**Fix**: Bound iterations and prefer stack allocation:
```rust
const MAX_BATCH_SIZE: usize = 32;

pub fn process_batch(ctx: Context<ProcessBatch>, offset: u32, count: u32) -> Result<()> {
    let count = std::cmp::min(count as usize, MAX_BATCH_SIZE);

    // Use fixed-size stack array when possible
    let mut results = [0u64; MAX_BATCH_SIZE];
    for i in 0..count {
        results[i] = process_item(offset + i as u32)?;
    }
    Ok(())
}
```

**Rules**:
- [ ] Bound all loop iterations with constants
- [ ] Limit Vec allocations (32KB heap total)
- [ ] Use stack allocation (`[T; N]`) when size is known
- [ ] Split large operations across multiple transactions

### 30. Account Constraint Fragility

**Severity**: Medium

Complex Anchor constraints can have subtle edge cases with zero values, max values, or same-account parameters.

```rust
// VULNERABLE -- constraint doesn't handle edge case
#[account(
    constraint = user_state.staked_amount > 0 @ ErrorCode::NoStake
)]
pub user_state: Account<'info, UserState>,
// What if staked_amount was set to u64::MAX due to overflow?
// The constraint passes, but the state is corrupted
```

**Fix**: Test edge cases explicitly and add multiple constraint layers:
```rust
#[account(
    constraint = user_state.staked_amount > 0 @ ErrorCode::NoStake,
    constraint = user_state.staked_amount <= MAX_STAKE @ ErrorCode::InvalidStake,
    constraint = user_state.owner == user.key() @ ErrorCode::Unauthorized,
)]
pub user_state: Account<'info, UserState>,
```

**Testing checklist**:
- [ ] Zero values for all numeric fields
- [ ] `u64::MAX` / `i64::MAX` / `i64::MIN` values
- [ ] Same account passed for two different parameters
- [ ] Empty strings and max-length strings
- [ ] Expired timestamps

### 31. Ed25519 Introspection

**Severity**: High

Ed25519 signature verification via instruction introspection can be bypassed if the program doesn't validate the instruction's position, pubkey, message, and signature properly.

```rust
// VULNERABLE -- doesn't validate instruction position or full signature data
pub fn verify_sig(ctx: Context<VerifySig>) -> Result<()> {
    let ix = load_instruction_at_checked(0, &ctx.accounts.instructions)?;
    // Assumes index 0 is always the Ed25519 instruction -- attacker can reorder!
    require!(ix.program_id == ed25519_program::ID, ErrorCode::InvalidProgram);
    // Doesn't validate pubkey, message, or signature content
    Ok(())
}
```

**Fix**: Validate instruction position, program ID, pubkey, message, and prevent reuse:
```rust
pub fn verify_sig(
    ctx: Context<VerifySig>,
    expected_message: Vec<u8>,
    sig_instruction_index: u8,
) -> Result<()> {
    let ix = load_instruction_at_checked(
        sig_instruction_index as usize,
        &ctx.accounts.instructions,
    )?;

    // Validate it's the Ed25519 program
    require!(ix.program_id == ed25519_program::ID, ErrorCode::InvalidProgram);

    // Parse and validate the signature data
    let sig_data = Ed25519InstructionData::unpack(&ix.data)?;

    // Validate the signing pubkey
    require!(
        sig_data.public_key == ctx.accounts.expected_signer.key().to_bytes(),
        ErrorCode::InvalidSigner
    );

    // Validate the message matches expected
    require!(sig_data.message == expected_message, ErrorCode::InvalidMessage);

    // Prevent signature reuse with a nonce
    let nonce_account = &mut ctx.accounts.nonce_account;
    require!(!nonce_account.used, ErrorCode::SignatureAlreadyUsed);
    nonce_account.used = true;

    Ok(())
}
```

**Key rule**: Always validate instruction position, program ID, pubkey, message content, and signature. Use nonces to prevent replay attacks.

---

## Case Studies

### Case 1: Wormhole Bridge Hack -- Sysvar Not Checked

The `verify_signatures` function used `load_current_index()` without validating that the sysvar account was actually the Instructions sysvar. An attacker passed a fake account.

```rust
// VULNERABLE
let current_instruction = solana_program::sysvar::instructions::load_current_index(
    &accs.instruction_acc.try_borrow_mut_data()?,
);
```

**Fix**: Validate sysvar address before use:
```rust
if *accs.instruction_acc.key != solana_program::sysvar::instructions::id() {
    return Err(SolitaireError::InvalidSysvar(*accs.instruction_acc.key));
}
let current_instruction = solana_program::sysvar::instructions::load_current_index(
    &accs.instruction_acc.try_borrow_mut_data()?,
);
```

**Impact**: $320M+ loss in the Wormhole bridge exploit.

### Case 2: PDA Account Without Caller/Beneficiary Validation

A DeFi protocol used a PDA as the vault authority, but the withdrawal function only verified the depositor's signature -- not that the depositor owned the deposit notes being burned. Any signed caller could burn another user's tokens and redirect funds.

**Root cause**: The `deposit_note_account` and `withdraw_account` were not derived from or validated against the depositor.

**Fix**: Derive the deposit account PDA from both `reserve.key()` and `depositor.key()` as seeds, ensuring only the depositor can interact with their own deposit:
```rust
#[account(mut,
    seeds = [
        b"deposits".as_ref(),
        reserve.key().as_ref(),
        depositor.key.as_ref()  // Ties deposit to this specific depositor
    ],
    bump = bump)]
pub deposit_account: AccountInfo<'info>,
```

### Case 3: Mango Markets -- Price Manipulation

**Impact**: $115M loss (October 2022)

Attacker manipulated the MNGO/USD oracle price on a thin-liquidity market by buying massive MNGO-PERP positions across two accounts, then pumping the spot price. The inflated collateral value let the attacker borrow $115M from Mango's lending pools.

**Root cause**: No oracle sanity checks, no position size limits, thin liquidity on the MNGO market allowed price manipulation.

**Lessons**:
- [ ] Validate oracle prices against TWAP or multiple sources
- [ ] Implement position size limits relative to market liquidity
- [ ] Add circuit breakers for abnormal price movements
- [ ] Check oracle confidence intervals (`conf` field in Pyth)

### Case 4: Cashio -- Missing Account Validation

**Impact**: $48M loss (March 2022)

The Cashio CASH stablecoin minting function failed to validate that the `bank` account passed to the `mint_collateral` instruction actually matched the protocol's expected bank. An attacker passed a fake bank with a worthless token as collateral and minted unlimited CASH tokens.

**Root cause**: The `bank` account in the `BurnCash` / `MintCash` instructions was not validated against a known set of approved banks. No `has_one` or `seeds` constraint linked it.

**Lessons**:
- [ ] Every account in a financial instruction must be validated (PDA, `has_one`, or whitelist)
- [ ] Never trust accounts passed by users without ownership/derivation checks
- [ ] Protocol-critical accounts (banks, oracles, vaults) must be derived from or linked to known roots
