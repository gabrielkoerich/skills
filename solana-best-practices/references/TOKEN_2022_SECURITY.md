# Token-2022 Extension Security

Security considerations for SPL Token-2022 (Token Extensions Program). Token-2022 introduces extensions that change fundamental assumptions about token behavior.

Sources: [Zealynx Security Checklist](https://www.zealynx.io/blogs/solana-security-checklist), [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security)

---

## Token-Agnostic Interface

**Severity**: High

Programs hardcoded for SPL Token will break with Token-2022 tokens. Token-2022 uses a different program ID.

```rust
// VULNERABLE -- only works with SPL Token, ignores Token-2022
use anchor_spl::token::{self, Token, Transfer};

#[derive(Accounts)]
pub struct TransferTokens<'info> {
    pub token_program: Program<'info, Token>, // Rejects Token-2022 tokens!
}

// In handler:
token::transfer(cpi_ctx, amount)?; // No decimal validation
```

**Fix**: Use `token_interface` and `transfer_checked` for both SPL Token and Token-2022:
```rust
use anchor_spl::token_interface::{self, TokenInterface, TransferChecked, Mint, TokenAccount};

#[derive(Accounts)]
pub struct TransferTokens<'info> {
    #[account(mut)]
    pub from: InterfaceAccount<'info, TokenAccount>,
    #[account(mut)]
    pub to: InterfaceAccount<'info, TokenAccount>,
    pub mint: InterfaceAccount<'info, Mint>,
    pub authority: Signer<'info>,
    pub token_program: Interface<'info, TokenInterface>, // Accepts both programs
}

// In handler:
token_interface::transfer_checked(
    CpiContext::new(
        ctx.accounts.token_program.to_account_info(),
        TransferChecked {
            from: ctx.accounts.from.to_account_info(),
            to: ctx.accounts.to.to_account_info(),
            mint: ctx.accounts.mint.to_account_info(),
            authority: ctx.accounts.authority.to_account_info(),
        },
    ),
    amount,
    ctx.accounts.mint.decimals, // Validates decimals match
)?;
```

**Key rule**: Always use `Interface<'info, TokenInterface>` instead of `Program<'info, Token>` and `transfer_checked` instead of `transfer`.

---

## Pre-created ATAs

**Severity**: Medium

Using `init` for associated token accounts fails if the ATA already exists (e.g., user already received tokens from another source).

```rust
// VULNERABLE -- fails if ATA already exists
#[account(
    init,
    payer = user,
    associated_token::mint = mint,
    associated_token::authority = user,
)]
pub user_ata: Account<'info, TokenAccount>,
```

**Fix**: Use `init_if_needed` to handle existing ATAs:
```rust
#[account(
    init_if_needed,
    payer = user,
    associated_token::mint = mint,
    associated_token::authority = user,
)]
pub user_ata: Account<'info, TokenAccount>,
```

**Note**: Requires `anchor-lang = { features = ["init-if-needed"] }`. Be aware that `init_if_needed` requires careful use -- ensure the account is validated in all cases, not just the init path.

---

## SPL Token Validation

**Severity**: High

Accepting any token account without validating the mint allows attackers to use worthless tokens.

```rust
// VULNERABLE -- no mint validation
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)]
    pub user_token: Account<'info, TokenAccount>, // Any mint accepted!
    #[account(mut)]
    pub vault_token: Account<'info, TokenAccount>,
}
```

**Fix**: Validate mint, authority, and frozen state:
```rust
#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(
        mut,
        constraint = user_token.mint == vault_token.mint @ ErrorCode::MintMismatch,
        constraint = user_token.owner == user.key() @ ErrorCode::InvalidOwner,
        constraint = !user_token.is_frozen() @ ErrorCode::AccountFrozen,
    )]
    pub user_token: Account<'info, TokenAccount>,
    #[account(
        mut,
        constraint = vault_token.mint == expected_mint.key() @ ErrorCode::InvalidMint,
    )]
    pub vault_token: Account<'info, TokenAccount>,
    pub expected_mint: Account<'info, Mint>,
    pub user: Signer<'info>,
}
```

**Checklist**:
- [ ] Validate `token_account.mint == expected_mint`
- [ ] Validate `token_account.owner == expected_authority`
- [ ] Check `!token_account.is_frozen()`
- [ ] For deposits: verify the mint is the one your protocol expects

---

## CPIGuard Extension

**Severity**: High

Token-2022 accounts with CPIGuard enabled reject certain CPI operations (transfers, approvals, closes) to protect users from malicious programs.

```rust
// VULNERABLE -- will fail silently or panic with CPIGuard-enabled accounts
token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
// If the source account has CPIGuard enabled, this CPI will be rejected
```

**Fix**: Check for CPIGuard before CPI and provide fallback flows:
```rust
use spl_token_2022::extension::{BaseStateWithExtensions, StateWithExtensions};
use spl_token_2022::extension::cpi_guard::CpiGuard;
use spl_token_2022::state::Account as Token2022Account;

// Check if CPIGuard is enabled
let account_data = ctx.accounts.source.to_account_info().try_borrow_data()?;
let account_state = StateWithExtensions::<Token2022Account>::unpack(&account_data)?;

if let Ok(cpi_guard) = account_state.get_extension::<CpiGuard>() {
    if cpi_guard.lock_cpi.into() {
        return err!(ErrorCode::CpiGuardEnabled);
        // Inform user to perform the transfer as a top-level instruction instead
    }
}

// Safe to proceed with CPI
token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
```

**Key rule**: Always handle the case where CPI operations may be blocked by CPIGuard. Provide user-facing error messages or alternative instruction flows.

---

## Default Account State Extension

**Severity**: Medium

Mints with the `DefaultAccountState` extension can create token accounts that start frozen. Programs assuming new accounts are active will fail.

```rust
// VULNERABLE -- assumes newly created ATA is immediately usable
let cpi_ctx = CpiContext::new(/* ... */);
token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
// Fails if the destination account was created frozen by default!
```

**Fix**: Check the mint's default account state and thaw if needed:
```rust
use spl_token_2022::extension::default_account_state::DefaultAccountState;

// Check if mint creates frozen accounts by default
let mint_data = ctx.accounts.mint.to_account_info().try_borrow_data()?;
let mint_state = StateWithExtensions::<spl_token_2022::state::Mint>::unpack(&mint_data)?;

if let Ok(default_state) = mint_state.get_extension::<DefaultAccountState>() {
    if u8::from(default_state.state) == spl_token_2022::state::AccountState::Frozen as u8 {
        // Must thaw the account before transferring
        // Or reject this mint if your protocol doesn't support frozen defaults
        return err!(ErrorCode::MintCreatesAccountsFrozen);
    }
}
```

**Key rule**: Never assume new token accounts are active. Check the mint's `DefaultAccountState` extension.

---

## Mint Close Authority Extension

**Severity**: High

Token-2022 mints with a `MintCloseAuthority` can be closed after all tokens are burned. Programs holding references to such mints may encounter closed accounts.

```rust
// VULNERABLE -- assumes mint always exists
pub fn check_supply(ctx: Context<CheckSupply>) -> Result<()> {
    let supply = ctx.accounts.mint.supply; // Panics if mint was closed!
    Ok(())
}
```

**Fix**: Verify mint existence before operations:
```rust
pub fn check_supply(ctx: Context<CheckSupply>) -> Result<()> {
    // Verify the mint account still has data
    let mint_info = ctx.accounts.mint.to_account_info();
    require!(mint_info.data_len() > 0, ErrorCode::MintClosed);
    require!(**mint_info.try_borrow_lamports()? > 0, ErrorCode::MintClosed);

    let supply = ctx.accounts.mint.supply;
    Ok(())
}
```

**Key rule**: If your protocol accepts arbitrary mints, check for `MintCloseAuthority` and handle the case where the mint may no longer exist.

---

## Permanent Delegate Extension

**Severity**: Critical

Token-2022 mints with a `PermanentDelegate` allow the delegate to transfer or burn tokens from ANY account of that mint, without the owner's consent.

```rust
// DANGEROUS -- depositing a token with permanent delegate
// The permanent delegate can reclaim ALL deposited tokens at any time!
pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    // Even after this transfer, the permanent delegate can steal the tokens
    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
    Ok(())
}
```

**Fix**: Check for permanent delegate before accepting deposits:
```rust
use spl_token_2022::extension::permanent_delegate::PermanentDelegate;

pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    let mint_data = ctx.accounts.mint.to_account_info().try_borrow_data()?;
    let mint_state = StateWithExtensions::<spl_token_2022::state::Mint>::unpack(&mint_data)?;

    // Reject tokens with permanent delegates -- funds are never safe
    if mint_state.get_extension::<PermanentDelegate>().is_ok() {
        return err!(ErrorCode::PermanentDelegateNotAllowed);
    }

    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
    Ok(())
}
```

**Key rule**: NEVER accept deposits of tokens with a permanent delegate unless your protocol explicitly accounts for the risk. The delegate can drain all vaults at any time.

---

## Transfer Hook Extension

**Severity**: High

Token-2022 mints with `TransferHook` execute custom program logic on every transfer. This has compute and security implications.

**Compute risk**: Transfer hooks consume additional compute units. A heavy hook can cause your transaction to exceed the CU budget.

**Security risk**: The hook program can enforce additional constraints or fail transfers unexpectedly.

```rust
// VULNERABLE -- no extra CU budget for hook execution
pub fn process_transfer(ctx: Context<ProcessTransfer>, amount: u64) -> Result<()> {
    // If mint has a transfer hook, this may fail with out-of-compute-budget
    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;
    Ok(())
}
```

**Fix**: Budget extra compute units and handle hook failures:
```rust
// Client-side: add extra compute budget
let compute_ix = ComputeBudgetInstruction::set_compute_unit_limit(400_000); // Extra CU
let transfer_ix = /* your transfer instruction */;
let tx = Transaction::new_signed_with_payer(
    &[compute_ix, transfer_ix],
    Some(&payer.pubkey()),
    &[&payer],
    recent_blockhash,
);

// Program-side: handle potential hook failures gracefully
pub fn process_transfer(ctx: Context<ProcessTransfer>, amount: u64) -> Result<()> {
    token_interface::transfer_checked(cpi_ctx, amount, decimals)
        .map_err(|e| {
            msg!("Transfer failed (possibly due to transfer hook): {:?}", e);
            ErrorCode::TransferFailed
        })?;
    Ok(())
}
```

**Key rule**: When working with arbitrary Token-2022 mints, always budget extra CU for potential transfer hooks. Test with hook-enabled tokens.

---

## Transfer Fee Extension

**Severity**: High

Token-2022 mints with `TransferFee` withhold a percentage of each transfer. The received amount is less than the sent amount.

```rust
// VULNERABLE -- assumes received == sent
pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;

    // BUG: If mint has transfer fee, vault received LESS than `amount`
    ctx.accounts.user_state.deposited += amount; // Over-credits the user!
    Ok(())
}
```

**Fix**: Account for transfer fees in calculations:
```rust
use spl_token_2022::extension::transfer_fee::TransferFeeConfig;

pub fn deposit(ctx: Context<Deposit>, amount: u64) -> Result<()> {
    // Calculate actual received amount after fees
    let mint_data = ctx.accounts.mint.to_account_info().try_borrow_data()?;
    let mint_state = StateWithExtensions::<spl_token_2022::state::Mint>::unpack(&mint_data)?;

    let actual_amount = if let Ok(fee_config) = mint_state.get_extension::<TransferFeeConfig>() {
        let epoch = Clock::get()?.epoch;
        let fee = fee_config
            .calculate_epoch_fee(epoch, amount)
            .ok_or(ErrorCode::FeeCalculationFailed)?;
        amount.checked_sub(fee).ok_or(ErrorCode::Overflow)?
    } else {
        amount // No transfer fee extension
    };

    token_interface::transfer_checked(cpi_ctx, amount, decimals)?;

    // Credit the ACTUAL received amount, not the sent amount
    ctx.accounts.user_state.deposited = ctx.accounts.user_state.deposited
        .checked_add(actual_amount)
        .ok_or(ErrorCode::Overflow)?;
    Ok(())
}
```

**Key rule**: NEVER assume `received == sent`. Always check for `TransferFeeConfig` and calculate the actual received amount. Use `transfer_checked` which handles fees automatically on the token side.

---

## Token-2022 Security Checklist

Before integrating Token-2022 tokens:

- [ ] Use `Interface<'info, TokenInterface>` and `InterfaceAccount` types
- [ ] Use `transfer_checked` instead of `transfer`
- [ ] Check for `PermanentDelegate` -- reject or handle appropriately
- [ ] Check for `TransferFee` -- adjust accounting for withheld fees
- [ ] Check for `TransferHook` -- budget extra compute units
- [ ] Check for `CPIGuard` -- provide fallback instruction flows
- [ ] Check for `DefaultAccountState` -- handle frozen-by-default accounts
- [ ] Check for `MintCloseAuthority` -- handle potentially closed mints
- [ ] Use `init_if_needed` for ATAs, not `init`
- [ ] Validate mint, owner, and frozen state on all token accounts
