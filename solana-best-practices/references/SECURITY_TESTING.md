# Security Testing Patterns

TDD-style test patterns for discovering and verifying fixes for each vulnerability class. For every vulnerability found, the workflow is:

1. **Write an exploit test** that proves the vulnerability exists (test PASSES = vulnerability confirmed)
2. **Apply the fix** to the program code
3. **Run the test again** to confirm the exploit is now blocked (test PASSES = fix verified)

All tests use Anchor's TypeScript testing framework with `@coral-xyz/anchor` and `solana-bankrun` where applicable.

Sources: [Zealynx Security Checklist](https://www.zealynx.io/blogs/solana-security-checklist), [Helius Security Guide](https://www.helius.dev/blog/a-hitchhikers-guide-to-solana-program-security)

---

## Index

- [Test Setup](#test-setup)
- [V1-4: Arithmetic Exploits](#v1-4-arithmetic-exploits)
- [V6-7: Missing Signer / Permission](#v6-7-missing-signer--permission)
- [V8-9: Missing Writable / Owner Check](#v8-9-missing-writable--owner-check)
- [V10: Re-initialization](#v10-re-initialization)
- [V11: PDA Substitution](#v11-pda-substitution)
- [V12: Fake System Account](#v12-fake-system-account)
- [V17: Unsafe Casting](#v17-unsafe-casting)
- [V18: Authority Transfer](#v18-authority-transfer)
- [V20: CPI Signer Forwarding](#v20-cpi-signer-forwarding)
- [V21: Dependency Chain](#v21-dependency-chain)
- [V22: Frontrunning / Slippage](#v22-frontrunning--slippage)
- [V23: Remaining Accounts](#v23-remaining-accounts)
- [V26: Seed Collisions](#v26-seed-collisions)
- [Token-2022: Transfer Fees](#token-2022-transfer-fees)
- [Token-2022: Permanent Delegate](#token-2022-permanent-delegate)
- [Duplicate Mutable Accounts](#duplicate-mutable-accounts)
- [Account Closing / Revival](#account-closing--revival)
- [Account Reloading After CPI](#account-reloading-after-cpi)

---

## Test Setup

```typescript
import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Keypair, SystemProgram, PublicKey } from "@solana/web3.js";
import { assert, expect } from "chai";
import { MyProgram } from "../target/types/my_program";

describe("security tests", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  const program = anchor.workspace.MyProgram as Program<MyProgram>;

  // Helper: expect a transaction to fail with a specific error
  async function expectError(promise: Promise<any>, errorCode: string) {
    try {
      await promise;
      assert.fail("Transaction should have failed");
    } catch (err: any) {
      if (err.error?.errorCode?.code) {
        expect(err.error.errorCode.code).to.equal(errorCode);
      } else if (err.message) {
        expect(err.message).to.include(errorCode);
      } else {
        throw err;
      }
    }
  }

  // Helper: expect a transaction to fail (any error)
  async function expectFailure(promise: Promise<any>, message?: string) {
    try {
      await promise;
      assert.fail(message || "Transaction should have failed");
    } catch (err: any) {
      if (err.message?.includes("should have failed")) throw err;
      // Transaction failed as expected
    }
  }
});
```

---

## V1-4: Arithmetic Exploits

### Discover: Overflow wraps to zero

```typescript
it("EXPLOIT: overflow wraps balance to zero", async () => {
  // Setup: user has balance near u64::MAX
  const userState = await setupUserWithBalance(new anchor.BN("18446744073709551610")); // u64::MAX - 5

  // Exploit: deposit amount that causes overflow
  await program.methods
    .deposit(new anchor.BN("10")) // 18446744073709551610 + 10 wraps to 4
    .accounts({ userState, user: attacker.publicKey })
    .signers([attacker])
    .rpc();

  // Verify: balance wrapped around (vulnerability confirmed)
  const account = await program.account.userState.fetch(userState);
  assert.isTrue(account.balance.lt(new anchor.BN("10")), "Balance wrapped -- overflow!");
});
```

### Verify fix: Overflow rejected

```typescript
it("FIX: overflow is rejected with checked arithmetic", async () => {
  const userState = await setupUserWithBalance(new anchor.BN("18446744073709551610"));

  await expectError(
    program.methods
      .deposit(new anchor.BN("10"))
      .accounts({ userState, user: user.publicKey })
      .signers([user])
      .rpc(),
    "Overflow" // Custom error from checked_add().ok_or(ErrorCode::Overflow)
  );
});
```

### Discover: Division by zero

```typescript
it("EXPLOIT: division by zero panics the program", async () => {
  // Setup: pool with zero total supply
  const pool = await setupPoolWithSupply(0);

  await expectFailure(
    program.methods
      .calculateShare(new anchor.BN("1000"))
      .accounts({ pool })
      .rpc(),
    "Division by zero should panic the program"
  );
});
```

---

## V6-7: Missing Signer / Permission

### Discover: Anyone can call admin function

```typescript
it("EXPLOIT: non-admin can initialize config", async () => {
  const attacker = Keypair.generate();
  await airdrop(attacker.publicKey, 1);

  // Exploit: attacker calls init function meant for admin only
  await program.methods
    .initializeConfig()
    .accounts({
      config: configPda,
      authority: attacker.publicKey, // Not the real admin!
      systemProgram: SystemProgram.programId,
    })
    .signers([attacker])
    .rpc();

  // Verify: attacker is now the authority (vulnerability confirmed)
  const config = await program.account.config.fetch(configPda);
  assert.ok(config.authority.equals(attacker.publicKey), "Attacker became admin!");
});
```

### Verify fix: Non-admin rejected

```typescript
it("FIX: non-admin cannot initialize config", async () => {
  const attacker = Keypair.generate();
  await airdrop(attacker.publicKey, 1);

  await expectFailure(
    program.methods
      .initializeConfig()
      .accounts({
        config: configPda,
        authority: attacker.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .signers([attacker])
      .rpc(),
    "Non-admin should be rejected"
  );
});
```

### Discover: Missing signer check

```typescript
it("EXPLOIT: unsigned authority can withdraw", async () => {
  // Exploit: pass victim's pubkey as authority WITHOUT their signature
  // Only works if program checks key but not is_signer
  await program.methods
    .withdraw(new anchor.BN("1000000"))
    .accounts({
      vault: vaultPda,
      authority: victim.publicKey, // Correct key, but attacker controls tx
      destination: attacker.publicKey,
    })
    // NOTE: victim is NOT in signers array
    .signers([attacker])
    .rpc();

  // If this succeeds, the signer check is missing
});
```

---

## V8-9: Missing Writable / Owner Check

### Discover: Fake account with crafted data

```typescript
it("EXPLOIT: fake oracle account accepted", async () => {
  // Create a fake account that mimics oracle data
  const fakeOracle = Keypair.generate();
  const fakePrice = Buffer.alloc(64);
  fakePrice.writeBigUInt64LE(BigInt(999999999), 0); // Inflated price

  // Create account owned by attacker's program (not Pyth)
  await createAccountWithData(fakeOracle, fakePrice, attackerProgram.programId);

  // Exploit: use fake oracle
  await program.methods
    .borrow(new anchor.BN("1000000"))
    .accounts({
      oracle: fakeOracle.publicKey, // Fake -- not owned by Pyth
      vault: vaultPda,
      borrower: attacker.publicKey,
    })
    .signers([attacker])
    .rpc();
});
```

### Verify fix: Wrong owner rejected

```typescript
it("FIX: account with wrong owner is rejected", async () => {
  const fakeOracle = Keypair.generate();
  await createAccountWithData(fakeOracle, fakeData, attackerProgram.programId);

  await expectError(
    program.methods
      .borrow(new anchor.BN("1000000"))
      .accounts({
        oracle: fakeOracle.publicKey,
        vault: vaultPda,
        borrower: attacker.publicKey,
      })
      .signers([attacker])
      .rpc(),
    "AccountOwnedByWrongProgram"
  );
});
```

---

## V10: Re-initialization

### Discover: Account can be re-initialized

```typescript
it("EXPLOIT: re-initialize to take over config", async () => {
  // Setup: config already initialized by legitimate admin
  await program.methods.initializeConfig().accounts({ /* ... */ }).signers([admin]).rpc();

  // Exploit: attacker re-initializes the same config
  await program.methods
    .initializeConfig()
    .accounts({
      config: configPda,
      authority: attacker.publicKey,
      systemProgram: SystemProgram.programId,
    })
    .signers([attacker])
    .rpc();

  // Verify: attacker overwrote the authority
  const config = await program.account.config.fetch(configPda);
  assert.ok(config.authority.equals(attacker.publicKey), "Config re-initialized by attacker!");
});
```

---

## V11: PDA Substitution

### Discover: Fake PDA base account

```typescript
it("EXPLOIT: use fake config to derive unauthorized PDA", async () => {
  // Create a fake config account with attacker as authority
  const fakeConfig = Keypair.generate();
  await createFakeConfigAccount(fakeConfig, attacker.publicKey);

  // Derive PDA from fake config
  const [fakePda] = PublicKey.findProgramAddressSync(
    [Buffer.from("vault"), fakeConfig.publicKey.toBuffer()],
    program.programId
  );

  // Exploit: use fake config to access vault
  await program.methods
    .withdraw(new anchor.BN("1000000"))
    .accounts({
      config: fakeConfig.publicKey, // Unconstrained!
      vault: fakePda,
      authority: attacker.publicKey,
    })
    .signers([attacker])
    .rpc();
});
```

---

## V12: Fake System Account

### Discover: Pass fake token program

```typescript
it("EXPLOIT: fake token program steals tokens", async () => {
  // Deploy a malicious token program that always succeeds
  const fakeTokenProgram = await deployMaliciousProgram();

  await program.methods
    .transfer(new anchor.BN("1000000"))
    .accounts({
      from: victimTokenAccount,
      to: attackerTokenAccount,
      authority: attacker.publicKey,
      tokenProgram: fakeTokenProgram.publicKey, // Fake!
    })
    .signers([attacker])
    .rpc();
});
```

### Verify fix: Wrong program ID rejected

```typescript
it("FIX: non-SPL token program is rejected", async () => {
  await expectError(
    program.methods
      .transfer(new anchor.BN("1000000"))
      .accounts({
        from: victimTokenAccount,
        to: attackerTokenAccount,
        authority: attacker.publicKey,
        tokenProgram: fakeTokenProgram.publicKey,
      })
      .signers([attacker])
      .rpc(),
    "InvalidProgramId"
  );
});
```

---

## V17: Unsafe Casting

### Discover: Truncation via `as` cast

```typescript
it("EXPLOIT: large amount truncated via u32 cast", async () => {
  // Amount: 4294967296 (u32::MAX + 1) -- truncates to 0 as u32
  const amount = new anchor.BN("4294967296");

  await program.methods
    .processPayment(amount)
    .accounts({ /* ... */ })
    .signers([user])
    .rpc();

  // Verify: payment processed as 0 due to truncation
  const receipt = await program.account.receipt.fetch(receiptPda);
  assert.equal(receipt.amount.toNumber(), 0, "Amount truncated to zero!");
});
```

---

## V18: Authority Transfer

### Discover: Authority lost to wrong address

```typescript
it("EXPLOIT: single-step transfer to invalid address locks program", async () => {
  const invalidKey = Keypair.generate().publicKey; // No one has the private key

  await program.methods
    .transferAuthority(invalidKey)
    .accounts({ config: configPda, authority: admin.publicKey })
    .signers([admin])
    .rpc();

  // Verify: program is now permanently locked
  const config = await program.account.config.fetch(configPda);
  assert.ok(config.authority.equals(invalidKey), "Authority transferred to unrecoverable key!");
});
```

### Verify fix: Two-step transfer works

```typescript
it("FIX: two-step authority transfer requires acceptance", async () => {
  const newAdmin = Keypair.generate();
  await airdrop(newAdmin.publicKey, 1);

  // Step 1: Nominate
  await program.methods
    .nominateAuthority(newAdmin.publicKey)
    .accounts({ config: configPda, authority: admin.publicKey })
    .signers([admin])
    .rpc();

  // Verify: authority hasn't changed yet
  let config = await program.account.config.fetch(configPda);
  assert.ok(config.authority.equals(admin.publicKey), "Authority should not change yet");

  // Step 2: Accept
  await program.methods
    .acceptAuthority()
    .accounts({ config: configPda, newAuthority: newAdmin.publicKey })
    .signers([newAdmin])
    .rpc();

  // Verify: authority changed
  config = await program.account.config.fetch(configPda);
  assert.ok(config.authority.equals(newAdmin.publicKey), "Authority should be new admin");
});
```

---

## V20: CPI Signer Forwarding

### Discover: User wallet drained via CPI

```typescript
it("EXPLOIT: malicious program drains user via forwarded signer", async () => {
  // User interacts with protocol, their wallet is forwarded as signer to CPI
  const userBalanceBefore = await getBalance(user.publicKey);

  await program.methods
    .interactWithProtocol()
    .accounts({
      user: user.publicKey,
      externalProgram: maliciousProgram.publicKey,
    })
    .signers([user])
    .rpc();

  const userBalanceAfter = await getBalance(user.publicKey);
  assert.isTrue(
    userBalanceAfter < userBalanceBefore - 1_000_000,
    "User's wallet was drained via CPI signer forwarding!"
  );
});
```

---

## V21: Dependency Chain

### Discover: Fake root breaks validation chain

```typescript
it("EXPLOIT: fake config poisons entire validation chain", async () => {
  // Create fake config pointing to attacker's vault
  const fakeConfig = await createFakeConfig(attacker.publicKey);
  const attackerVault = await createVaultLinkedTo(fakeConfig);
  const fakeUserState = await createUserStateLinkedTo(attackerVault, attacker.publicKey);

  // Exploit: entire chain is fake but internally consistent
  await program.methods
    .withdraw(new anchor.BN("1000000"))
    .accounts({
      config: fakeConfig,         // Root: unconstrained!
      vault: attackerVault,       // Links to fake config
      userState: fakeUserState,   // Links to attacker vault
      user: attacker.publicKey,
    })
    .signers([attacker])
    .rpc();
});
```

---

## V22: Frontrunning / Slippage

### Discover: Swap with no minimum output

```typescript
it("EXPLOIT: sandwich attack on unprotected swap", async () => {
  // Attacker front-runs: buy large amount to move price
  await manipulatePoolPrice(pool, "up");

  // Victim's swap executes at worse price
  await program.methods
    .swap(new anchor.BN("1000000"))
    .accounts({ pool: poolPda, user: victim.publicKey })
    .signers([victim])
    .rpc();

  // Attacker back-runs: sell to profit
  await manipulatePoolPrice(pool, "down");

  // Verify: victim received much less than expected
  const received = await getTokenBalance(victimTokenAccount);
  assert.isTrue(received < expectedMinimum, "Victim got sandwiched!");
});
```

### Verify fix: Slippage protection works

```typescript
it("FIX: swap with slippage protection rejects bad price", async () => {
  await manipulatePoolPrice(pool, "up");

  await expectError(
    program.methods
      .swap(
        new anchor.BN("1000000"),
        new anchor.BN("950000"),   // minimum_amount_out
        new anchor.BN(Date.now() / 1000 + 60), // deadline
      )
      .accounts({ pool: poolPda, user: victim.publicKey })
      .signers([victim])
      .rpc(),
    "SlippageExceeded"
  );
});
```

---

## V23: Remaining Accounts

### Discover: Fake account in remaining_accounts

```typescript
it("EXPLOIT: inject fake account via remaining_accounts", async () => {
  // Create a fake user state with inflated balance
  const fakeUserState = Keypair.generate();
  await createAccountWithData(fakeUserState, fakeData, Keypair.generate().publicKey);

  await program.methods
    .processBatch()
    .accounts({ authority: attacker.publicKey })
    .remainingAccounts([
      { pubkey: fakeUserState.publicKey, isSigner: false, isWritable: true },
    ])
    .signers([attacker])
    .rpc();
});
```

---

## V26: Seed Collisions

### Discover: Two features share same PDA

```typescript
it("EXPLOIT: user vault and admin vault collide", async () => {
  // If admin is also a user, and seeds don't differentiate:
  // seeds = ["vault", admin.key()] == seeds = ["vault", user.key()] when admin == user
  const [userVault] = PublicKey.findProgramAddressSync(
    [Buffer.from("vault"), admin.publicKey.toBuffer()],
    program.programId
  );
  const [adminVault] = PublicKey.findProgramAddressSync(
    [Buffer.from("vault"), admin.publicKey.toBuffer()],
    program.programId
  );

  assert.ok(userVault.equals(adminVault), "PDAs collide -- same account for user and admin!");
});
```

### Verify fix: Distinct prefixes prevent collision

```typescript
it("FIX: user_vault and admin_vault have distinct PDAs", async () => {
  const [userVault] = PublicKey.findProgramAddressSync(
    [Buffer.from("user_vault"), admin.publicKey.toBuffer()],
    program.programId
  );
  const [adminVault] = PublicKey.findProgramAddressSync(
    [Buffer.from("admin_vault"), admin.publicKey.toBuffer()],
    program.programId
  );

  assert.notOk(userVault.equals(adminVault), "PDAs should be different");
});
```

---

## Token-2022: Transfer Fees

### Discover: Accounting error with fee tokens

```typescript
it("EXPLOIT: deposit over-credits due to transfer fee", async () => {
  // Token has 5% transfer fee
  const depositAmount = new anchor.BN("1000000");

  await program.methods
    .deposit(depositAmount)
    .accounts({
      userToken: userAta,
      vault: vaultAta,
      mint: feeTokenMint,
      user: user.publicKey,
      tokenProgram: TOKEN_2022_PROGRAM_ID,
    })
    .signers([user])
    .rpc();

  // Verify: user credited full amount, but vault received 950000
  const userState = await program.account.userState.fetch(userStatePda);
  const vaultBalance = await getTokenBalance(vaultAta);

  assert.equal(userState.deposited.toNumber(), 1000000, "User over-credited!");
  assert.equal(vaultBalance, 950000, "Vault only received 950k");
  // Insolvency: users can withdraw more than vault holds
});
```

### Verify fix: Fee-adjusted accounting

```typescript
it("FIX: deposit credits actual received amount after fees", async () => {
  const depositAmount = new anchor.BN("1000000");

  await program.methods
    .deposit(depositAmount)
    .accounts({ /* ... */ })
    .signers([user])
    .rpc();

  const userState = await program.account.userState.fetch(userStatePda);
  const vaultBalance = await getTokenBalance(vaultAta);

  // User credited matches vault balance (fee-adjusted)
  assert.equal(userState.deposited.toNumber(), vaultBalance, "Credits should match actual received");
});
```

---

## Token-2022: Permanent Delegate

### Discover: Delegated tokens drained from vault

```typescript
it("EXPLOIT: permanent delegate drains vault after deposit", async () => {
  // User deposits token with permanent delegate
  await program.methods
    .deposit(new anchor.BN("1000000"))
    .accounts({ mint: permanentDelegateMint, /* ... */ })
    .signers([user])
    .rpc();

  // Permanent delegate reclaims all tokens from vault!
  await transferWithPermanentDelegate(
    vaultAta,              // source: protocol's vault
    attackerAta,           // destination: attacker
    permanentDelegate,     // authority: the permanent delegate
    1000000,
    TOKEN_2022_PROGRAM_ID
  );

  // Vault is drained, user state still shows balance
  const vaultBalance = await getTokenBalance(vaultAta);
  assert.equal(vaultBalance, 0, "Vault drained by permanent delegate!");
});
```

### Verify fix: Permanent delegate tokens rejected

```typescript
it("FIX: deposit rejects tokens with permanent delegate", async () => {
  await expectError(
    program.methods
      .deposit(new anchor.BN("1000000"))
      .accounts({ mint: permanentDelegateMint, /* ... */ })
      .signers([user])
      .rpc(),
    "PermanentDelegateNotAllowed"
  );
});
```

---

## Duplicate Mutable Accounts

### Discover: Same account passed twice

```typescript
it("EXPLOIT: pass same account as source and destination", async () => {
  // Transfer from account A to account A doubles the balance
  await program.methods
    .transfer(new anchor.BN("1000000"))
    .accounts({
      from: userTokenAccount,
      to: userTokenAccount,  // Same account!
      authority: user.publicKey,
    })
    .signers([user])
    .rpc();
});
```

### Verify fix: Duplicate accounts rejected

```typescript
it("FIX: same account for from and to is rejected", async () => {
  await expectError(
    program.methods
      .transfer(new anchor.BN("1000000"))
      .accounts({
        from: userTokenAccount,
        to: userTokenAccount,
        authority: user.publicKey,
      })
      .signers([user])
      .rpc(),
    "DuplicateAccounts"
  );
});
```

---

## Account Closing / Revival

### Discover: Closed account can be revived

```typescript
it("EXPLOIT: revive closed account within same transaction", async () => {
  // Close the account (zeroes lamports)
  await program.methods
    .closeAccount()
    .accounts({ account: targetPda, destination: user.publicKey })
    .signers([user])
    .rpc();

  // In same transaction or slot: re-fund the account
  await provider.connection.requestAirdrop(targetPda, 1_000_000);

  // Account is revived with stale/zeroed data -- can be exploited
  const accountInfo = await provider.connection.getAccountInfo(targetPda);
  assert.isNotNull(accountInfo, "Account revived after close!");
});
```

### Verify fix: Account has closed discriminator

```typescript
it("FIX: closed account has CLOSED discriminator and is rejected", async () => {
  await program.methods
    .closeAccount()
    .accounts({ account: targetPda, destination: user.publicKey })
    .signers([user])
    .rpc();

  // Even if account is re-funded, the CLOSED discriminator prevents reuse
  await expectError(
    program.methods
      .useAccount()
      .accounts({ account: targetPda })
      .rpc(),
    "AccountDiscriminatorMismatch"
  );
});
```

---

## Account Reloading After CPI

### Discover: Stale data after CPI

```typescript
it("EXPLOIT: stale supply after mint_to", async () => {
  const supplyBefore = (await getMint(mint)).supply;

  // Mint tokens via CPI
  const tx = await program.methods
    .mintAndCheck(new anchor.BN("1000"))
    .accounts({ mint, /* ... */ })
    .signers([authority])
    .rpc();

  // Check program logs for the supply value it read
  const logs = await getTransactionLogs(tx);
  const reportedSupply = parseSupplyFromLogs(logs);

  // If program didn't reload, it logged the OLD supply
  assert.equal(
    reportedSupply,
    supplyBefore.toString(),
    "Program used stale supply -- missing .reload()!"
  );
});
```

---

## Testing Workflow Summary

For each vulnerability class found during review:

### Phase 1: Prove the vulnerability (Red)
```
1. Write an exploit test that exercises the vulnerability
2. Run the test -- it should PASS (exploit succeeds)
3. Document the test as evidence of the vulnerability
```

### Phase 2: Apply the fix (Green)
```
1. Modify the program code to fix the vulnerability
2. Run the exploit test -- it should now FAIL (exploit blocked)
3. Add a new test that verifies the fix behavior
4. Run both tests -- exploit FAILS, fix verification PASSES
```

### Phase 3: Verify no regressions (Refactor)
```
1. Run the full test suite
2. Verify no existing tests broke
3. Add the new tests to the permanent test suite
```

### Test Categories to Always Include

For every Solana program, write tests for:

- [ ] **Happy path**: Normal operations work correctly
- [ ] **Wrong signer**: Non-authority cannot call privileged instructions
- [ ] **Wrong owner**: Accounts owned by wrong program are rejected
- [ ] **Overflow**: Maximum values don't wrap
- [ ] **Re-initialization**: Already-initialized accounts can't be overwritten
- [ ] **PDA substitution**: Wrong seeds fail derivation
- [ ] **Duplicate accounts**: Same account in two slots is rejected
- [ ] **Close and revive**: Closed accounts can't be reused
- [ ] **Stale data after CPI**: Account data is fresh after cross-program calls
- [ ] **Token-2022 edge cases**: Transfer fees, permanent delegates, CPI guards (if applicable)
