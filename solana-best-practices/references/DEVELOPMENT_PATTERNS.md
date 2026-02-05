# Development Patterns: Complete Reference

14 best practices for writing secure, efficient, and maintainable Solana/Anchor programs. Each pattern includes a vulnerable example and a secure fix.

---

## #1 Enforce Signer Checks on All Authority/Mutable Operations

**Category**: Security

**Rule**: Every instruction that mutates state, transfers value, or closes accounts must verify the caller's authority using `Signer<'info>` combined with `has_one`.

### Vulnerable

```rust
#[derive(Accounts)]
pub struct UpdateGreeting<'info> {
    #[account(mut)]
    pub greeting_account: Account<'info, GreetingAccount>,
    pub user: AccountInfo<'info>, // Anyone can call -- no signer check!
}

#[derive(Accounts)]
pub struct CloseGreeting<'info> {
    #[account(mut, close = user)]
    pub greeting_account: Account<'info, GreetingAccount>,
    #[account(mut)]
    pub user: AccountInfo<'info>, // Rent stolen by anyone!
}
```

### Secure

```rust
#[derive(Accounts)]
pub struct UpdateGreeting<'info> {
    #[account(
        mut,
        seeds = [b"greeting", owner.key().as_ref()],
        bump,
        has_one = owner @ ErrorCode::Unauthorized
    )]
    pub greeting_account: Account<'info, GreetingAccount>,
    pub owner: Signer<'info>, // Must sign to modify
}

#[derive(Accounts)]
pub struct CloseGreeting<'info> {
    #[account(
        mut,
        close = owner, // Rent goes back to owner
        seeds = [b"greeting", owner.key().as_ref()],
        bump,
        has_one = owner @ ErrorCode::Unauthorized
    )]
    pub greeting_account: Account<'info, GreetingAccount>,
    #[account(mut)]
    pub owner: Signer<'info>, // Must sign to close
}

#[error_code]
pub enum ErrorCode {
    #[msg("You are not authorized to perform this action")]
    Unauthorized,
}
```

**Checklist**:
- [ ] All authority/admin/owner accounts use `Signer<'info>`
- [ ] `has_one = owner` validates the stored owner field matches the signer
- [ ] `close = owner` sends rent refund to the rightful owner
- [ ] PDAs derived from signer key prevent account substitution

---

## #2 Always Use Typed Anchor Accounts Instead of Raw AccountInfo

**Category**: Security

**Rule**: Use `Account<'info, T>`, `Program<'info, T>`, and `Signer<'info>` for automatic validation. Only use `UncheckedAccount` when necessary, with a `/// CHECK:` comment explaining why.

### Vulnerable

```rust
#[derive(Accounts)]
pub struct TransferTokens<'info> {
    pub from_account: AccountInfo<'info>,   // Could be any account!
    pub to_account: AccountInfo<'info>,     // Could have wrong mint!
    pub authority: AccountInfo<'info>,       // No signer validation!
    pub token_program: AccountInfo<'info>,  // Could be fake program!
}
```

### Secure

```rust
#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(
        mut,
        constraint = from_account.owner == authority.key() @ ErrorCode::Unauthorized
    )]
    pub from_account: Account<'info, TokenAccount>,  // Validates owner == spl_token::ID

    #[account(
        mut,
        constraint = to_account.mint == from_account.mint @ ErrorCode::MintMismatch
    )]
    pub to_account: Account<'info, TokenAccount>,  // Validates structure + mint match

    pub authority: Signer<'info>,                   // Enforces signature
    pub token_program: Program<'info, Token>,       // Validates program ID
}

#[error_code]
pub enum ErrorCode {
    #[msg("You are not authorized to transfer from this account")]
    Unauthorized,
    #[msg("Token accounts must have the same mint")]
    MintMismatch,
}
```

**When `UncheckedAccount` is acceptable**:
- Read-only accounts where you only need the public key
- Accounts passed through to CPIs without deserialization
- Always add `/// CHECK:` with validation rationale

```rust
/// CHECK: This account is used for off-chain reference only.
/// We validate it's owned by Token Program but don't deserialize.
#[account(owner = anchor_spl::token::ID)]
pub mint_account: UncheckedAccount<'info>,
```

---

## #3 Validate Account Ownership and Data Constraints

**Category**: Security

**Rule**: Validate input lengths, enforce business logic constraints, track ownership in account data, and calculate account space correctly.

### Vulnerable

```rust
pub fn create_task(ctx: Context<CreateTask>, description: String) -> Result<()> {
    let task = &mut ctx.accounts.task;
    task.description = description; // No length check -- can overflow space!
    task.completed = false;
    // No owner field -- can't verify later!
    Ok(())
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(mut)] // No ownership validation!
    pub task: Account<'info, Task>,
    pub user: Signer<'info>,
}
```

### Secure

```rust
const MAX_DESCRIPTION_LENGTH: usize = 200;

pub fn create_task(ctx: Context<CreateTask>, description: String, task_id: u64) -> Result<()> {
    require!(description.len() <= MAX_DESCRIPTION_LENGTH, ErrorCode::DescriptionTooLong);
    require!(!description.is_empty(), ErrorCode::DescriptionEmpty);

    let task = &mut ctx.accounts.task;
    task.owner = ctx.accounts.user.key();
    task.description = description;
    task.completed = false;
    task.task_id = task_id;
    task.bump = ctx.bumps.task;
    task.created_at = Clock::get()?.unix_timestamp;
    Ok(())
}

#[derive(Accounts)]
pub struct CompleteTask<'info> {
    #[account(
        mut,
        seeds = [b"task", user.key().as_ref(), &task.task_id.to_le_bytes()],
        bump = task.bump,
        has_one = owner @ ErrorCode::Unauthorized
    )]
    pub task: Account<'info, Task>,
    pub user: Signer<'info>,
}

#[derive(Accounts)]
#[instruction(description: String, task_id: u64)]
pub struct CreateTask<'info> {
    #[account(
        init,
        payer = user,
        space = 8 +      // discriminator
                32 +     // owner: Pubkey
                4 + MAX_DESCRIPTION_LENGTH + // description: String (4-byte prefix + max)
                1 +      // completed: bool
                8 +      // task_id: u64
                1 +      // bump: u8
                8,       // created_at: i64
        seeds = [b"task", user.key().as_ref(), &task_id.to_le_bytes()],
        bump
    )]
    pub task: Account<'info, Task>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}
```

**Checklist**:
- [ ] All string/vec inputs have length validation with `require!`
- [ ] Account structs store an `owner: Pubkey` field
- [ ] `has_one = owner` enforces ownership on mutations
- [ ] Business logic constraints in `constraint = ...` (e.g., `!task.completed`)
- [ ] `#[instruction(...)]` makes parameters available in account validation

---

## #4 Use PDAs Correctly with Seeds and Bumps

**Category**: Security

**Rule**: Derive accounts with `seeds` and `bump`, store the bump, and validate with `has_one` to ensure only rightful owners can access their accounts.

### Vulnerable

```rust
#[derive(Accounts)]
pub struct Withdraw<'info> {
    pub user: Signer<'info>,
    #[account(mut)]
    pub vault: Account<'info, Vault>, // Anyone can pass any vault!
}
```

### Secure

```rust
#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        init,
        payer = user,
        space = 8 + 32 + 8 + 1,
        seeds = [b"vault", user.key().as_ref()],
        bump
    )]
    pub vault: Account<'info, Vault>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(
        mut,
        seeds = [b"vault", user.key().as_ref()],
        bump = vault.bump,        // Use stored bump (efficient)
        has_one = owner @ ErrorCode::Unauthorized
    )]
    pub vault: Account<'info, Vault>,
}

#[account]
pub struct Vault {
    pub owner: Pubkey,  // 32 bytes
    pub balance: u64,   // 8 bytes
    pub bump: u8,       // 1 byte -- store to avoid recomputation
}
```

**PDA rules**:
- [ ] Always derive with `seeds` containing user-specific data
- [ ] Store bump at init with `ctx.bumps.vault`
- [ ] Reuse stored bump with `bump = vault.bump` (avoids `find_program_address` cost)
- [ ] Combine with `has_one = owner` for double validation
- [ ] Include unique IDs in seeds when users need multiple accounts (e.g., `task_id`)

---

## #5 Validate All Inputs Rigorously

**Category**: Security

**Rule**: Use `checked_*()` arithmetic, validate ranges with constants, check array bounds, and verify timestamp ordering. Never use raw `+`, `-`, `*`, `/` on user-influenced values.

### Vulnerable

```rust
pub fn stake(ctx: Context<Stake>, amount: u64) -> Result<()> {
    let stake = &mut ctx.accounts.stake_account;
    stake.staked_amount += amount; // Can overflow in release!
    Ok(())
}

pub fn unstake(ctx: Context<Unstake>, amount: u64) -> Result<()> {
    let stake = &mut ctx.accounts.stake_account;
    stake.staked_amount -= amount; // Can underflow!
    Ok(())
}

pub fn claim_reward(ctx: Context<Claim>, index: u8) -> Result<()> {
    let stake = &ctx.accounts.stake_account;
    let reward = stake.rewards[index as usize]; // Array panic if out of bounds!
    Ok(())
}
```

### Secure

```rust
const MIN_STAKE: u64 = 1_000_000;
const MAX_STAKE: u64 = 1_000_000_000_000;

pub fn stake(ctx: Context<Stake>, amount: u64) -> Result<()> {
    require!(amount >= MIN_STAKE && amount <= MAX_STAKE, ErrorCode::InvalidAmount);

    let stake = &mut ctx.accounts.stake_account;
    stake.staked_amount = stake.staked_amount
        .checked_add(amount)
        .ok_or(ErrorCode::Overflow)?;
    stake.stake_timestamp = Clock::get()?.unix_timestamp;
    Ok(())
}

pub fn unstake(ctx: Context<Unstake>, amount: u64) -> Result<()> {
    let stake = &mut ctx.accounts.stake_account;
    require!(amount <= stake.staked_amount, ErrorCode::InsufficientBalance);

    stake.staked_amount = stake.staked_amount
        .checked_sub(amount)
        .ok_or(ErrorCode::Underflow)?;
    Ok(())
}

pub fn claim_reward(ctx: Context<Claim>, index: u8) -> Result<()> {
    let stake = &mut ctx.accounts.stake_account;
    require!((index as usize) < stake.rewards.len(), ErrorCode::InvalidIndex);

    let reward = stake.rewards[index as usize];
    require!(reward > 0, ErrorCode::NoReward);
    stake.rewards[index as usize] = 0;
    Ok(())
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid amount")] InvalidAmount,
    #[msg("Arithmetic overflow")] Overflow,
    #[msg("Arithmetic underflow")] Underflow,
    #[msg("Insufficient balance")] InsufficientBalance,
    #[msg("Invalid array index")] InvalidIndex,
    #[msg("No reward available")] NoReward,
}
```

**Validation checklist**:
- [ ] `checked_add()`, `checked_sub()`, `checked_mul()`, `checked_div()` for all arithmetic
- [ ] Range validation with MIN/MAX constants
- [ ] Array bounds: `require!(index < array.len())`
- [ ] Timestamp ordering: `require!(current_time >= previous_time)`
- [ ] Non-zero: `require!(amount > 0)` before operations
- [ ] Sufficient balance: `require!(amount <= balance)` before subtraction

---

## #6 Handle Errors Properly

**Category**: Reliability

**Rule**: Define custom error types with `#[error_code]`, use `require!` macros for early validation, never use `unwrap()` or `panic!` in production.

### Vulnerable

```rust
pub fn process(ctx: Context<Process>) -> Result<()> {
    let data = ctx.accounts.data.try_borrow_data().unwrap(); // Panics on failure!
    let value: u64 = data[0..8].try_into().unwrap();         // Panics on bad data!
    Ok(())
}
```

### Secure

```rust
#[error_code]
pub enum MyError {
    #[msg("Amount cannot be zero")]
    InvalidAmount,
    #[msg("Insufficient funds for withdrawal")]
    InsufficientFunds,
    #[msg("Account data is corrupted")]
    DataCorrupted,
}

pub fn process(ctx: Context<Process>, amount: u64) -> Result<()> {
    require!(amount > 0, MyError::InvalidAmount);
    require!(amount <= ctx.accounts.vault.balance, MyError::InsufficientFunds);

    // Return Result instead of panicking
    let data = ctx.accounts.data.try_borrow_data()
        .map_err(|_| error!(MyError::DataCorrupted))?;

    Ok(())
}
```

**Rules**:
- [ ] Define `#[error_code]` enum with descriptive `#[msg(...)]` for every failure mode
- [ ] Use `require!(condition, ErrorCode)` for early validation
- [ ] Replace all `unwrap()` with `.ok_or(ErrorCode)?` or `?`
- [ ] Never use `panic!`, `unreachable!`, or `todo!` in deployed code
- [ ] Anchor constraints (`has_one`, `constraint`) handle validation automatically -- use them

---

## #7 Calculate Account Space Correctly

**Category**: Correctness

**Rule**: Calculate exact byte sizes for all fields. Incorrect space causes silent data truncation or allocation failure.

### Formula

```
Total space = 8 (discriminator)
            + field sizes
```

| Type | Size |
|------|------|
| `bool` | 1 |
| `u8` / `i8` | 1 |
| `u16` / `i16` | 2 |
| `u32` / `i32` | 4 |
| `u64` / `i64` | 8 |
| `u128` / `i128` | 16 |
| `Pubkey` | 32 |
| `String` | 4 + max_length |
| `Vec<T>` | 4 + (max_count * sizeof(T)) |
| `Option<T>` | 1 + sizeof(T) |
| `[T; N]` | N * sizeof(T) |

### Example

```rust
#[account]
pub struct Task {
    pub owner: Pubkey,       // 32
    pub description: String, // 4 + 200 (max)
    pub completed: bool,     // 1
    pub task_id: u64,        // 8
    pub bump: u8,            // 1
    pub created_at: i64,     // 8
}
// Total: 8 + 32 + 204 + 1 + 8 + 1 + 8 = 262

#[account(
    init,
    payer = user,
    space = 8 + 32 + (4 + 200) + 1 + 8 + 1 + 8
)]
pub task: Account<'info, Task>,
```

**Rules**:
- [ ] Always include 8-byte discriminator
- [ ] Strings: `4 + max_length` (4-byte length prefix)
- [ ] Vecs: `4 + (max_count * element_size)`
- [ ] Options: `1 + inner_size` (1-byte presence flag)
- [ ] Define `MAX_*_LENGTH` constants and use them in both validation and space

---

## #8 Reload Accounts After CPI

**Category**: Correctness

**Rule**: After a CPI, Anchor's deserialized account structs hold stale data. Call `.reload()` before reading any fields that the CPI may have changed.

### Vulnerable

```rust
pub fn mint_and_check(ctx: Context<MintAndCheck>, amount: u64) -> Result<()> {
    anchor_spl::token::mint_to(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            MintTo {
                mint: ctx.accounts.mint.to_account_info(),
                to: ctx.accounts.user_ata.to_account_info(),
                authority: ctx.accounts.authority.to_account_info(),
            },
            signer_seeds,
        ),
        amount,
    )?;

    // BUG: mint.supply is STALE -- still shows pre-mint value!
    msg!("Supply: {}", ctx.accounts.mint.supply);
    Ok(())
}
```

### Secure

```rust
pub fn mint_and_check(ctx: Context<MintAndCheck>, amount: u64) -> Result<()> {
    anchor_spl::token::mint_to(/* ... */, amount)?;

    // Reload to get fresh data after CPI
    ctx.accounts.mint.reload()?;

    // Now supply reflects the mint
    msg!("Supply: {}", ctx.accounts.mint.supply);
    Ok(())
}
```

**When to reload**:
- [ ] After `token::transfer` -- reload source and destination token accounts
- [ ] After `token::mint_to` -- reload mint account (supply changed)
- [ ] After `token::burn` -- reload mint account and token account
- [ ] After any CPI that modifies an account you'll read from

---

## #9 Code Reusability

**Category**: Maintainability

**Rule**: Break programs into modular pieces. Use CPIs instead of reimplementing existing functionality. Extract shared logic into separate crates.

**Guidelines**:
- One instruction handler per function, doing one thing well
- Extract common validation into helper functions
- Use CPIs to call SPL Token, System Program, etc. instead of raw account manipulation
- Share types and utilities across programs via workspace crates
- Anchor's derive macros eliminate boilerplate -- use them fully

---

## #10 Comment and Document

**Category**: Maintainability

**Rule**: Write comments that explain *why*, not *what*. Document security assumptions, PDA derivations, and complex validation logic.

**Guidelines**:
- Use `///` for doc comments (generates `cargo doc` output)
- Always add `/// CHECK:` on `UncheckedAccount` explaining why it's safe
- Document PDA seeds and what makes them unique
- Explain non-obvious constraints and their security purpose
- Maintain a README with program architecture and setup steps

```rust
/// Withdraws tokens from the user's vault.
/// Only the original depositor (stored as `vault.owner`) can withdraw.
/// The vault PDA is derived from ["vault", user_pubkey], ensuring
/// each user has exactly one vault.
pub fn withdraw(ctx: Context<Withdraw>, amount: u64) -> Result<()> {
    // ...
}
```

---

## #11 Testing

**Category**: Quality

**Rule**: Test everything -- happy paths, failures, edge cases, and security boundaries.

**Strategy**:
- **Unit tests**: Individual functions, arithmetic, validation logic
- **Integration tests**: Full transactions via Anchor's test framework
- **Negative tests**: Verify errors are thrown for invalid inputs, wrong signers, bad accounts
- **State tests**: Verify account data changes correctly after operations
- **PDA tests**: Verify derivation and that wrong seeds fail

```typescript
describe("security tests", () => {
  it("rejects non-owner update", async () => {
    try {
      await program.methods.updateTask("hacked")
        .accounts({ task: victimTask, user: attacker.publicKey })
        .signers([attacker])
        .rpc();
      assert.fail("Should have rejected");
    } catch (err) {
      expect(err.error.errorCode.code).to.equal("Unauthorized");
    }
  });

  it("rejects overflow amount", async () => {
    try {
      await program.methods.stake(new anchor.BN("18446744073709551615"))
        .accounts({ stakeAccount, owner: user.publicKey })
        .signers([user])
        .rpc();
      assert.fail("Should have rejected");
    } catch (err) {
      expect(err.error.errorCode.code).to.equal("Overflow");
    }
  });
});
```

**Tools**: `anchor test`, `solana-bankrun` (faster local testing), `solana-test-validator`

---

## #12 Security Audits

**Category**: Quality

**Rule**: Get code audited before mainnet. Use firms that know Solana.

**Pre-audit checklist**:
- [ ] Run `cargo clippy` -- fix all warnings
- [ ] Run `cargo audit` -- no known vulnerable dependencies
- [ ] All `unwrap()` eliminated from production code
- [ ] Every `AccountInfo` has either a typed replacement or `/// CHECK:` justification
- [ ] Complete test suite with negative tests
- [ ] Documentation of program architecture and security assumptions

**Known Solana audit firms**: OtterSec, Neodyme, Trail of Bits, Sec3, Halborn

---

## #13 Upgradeability

**Category**: Operations

**Rule**: Plan for upgrades from day one. Use PDAs for storage, version accounts, and protect upgrade authority.

**Guidelines**:
- Solana programs are upgradeable by default through the upgrade authority
- Store all data in PDA accounts (persists across program upgrades)
- Add a `version: u8` field to account structs for migration
- Test upgrades on devnet first
- Use a multisig for the upgrade authority on mainnet
- When fully stable, consider making immutable with `solana program set-upgrade-authority <PROGRAM_ID> --final`

---

## #14 Compute Unit Management

**Category**: Performance

**Rule**: Profile instruction compute usage and optimize within the 200k-1.4M CU per transaction limit.

**Guidelines**:
- Profile with `solana logs` or transaction simulation to see CU usage
- Use `ComputeBudgetInstruction::set_compute_unit_limit()` when you need more CU
- Simulate transactions before sending to estimate costs
- Set reasonable priority fees with `ComputeBudgetInstruction::set_compute_unit_price()`
- Split heavy operations across multiple transactions
- Prefer fixed-size data at the start of account structs (faster deserialization)
- Minimize on-chain string operations and logging
