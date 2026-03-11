---
name: contract-decoder
description: "Decode and reverse-engineer smart contract binaries for security research. Solana: extract instructions, discriminators, PDAs, and error codes from .so files. EVM: decompile bytecode to recover function selectors and storage layout. Use for bug bounty recon, verifying deployed code, or analyzing closed-source contracts."
---

# Smart Contract Decoder

Decode deployed smart contract binaries to extract instructions, account structures, and attack surface — with or without source code. Built for bug bounty research on Immunefi, Code4rena, and similar platforms.

## Requirements

**Solana:**
- `solana` CLI (for `solana program dump`, `solana account`)
- `anchor` CLI (for `anchor idl fetch`)
- `objdump` (macOS: built-in llvm-objdump; Linux: binutils)
- `python3` with `hashlib` (for discriminator computation)
- `sha256sum` or `shasum` (for quick hashes)

**EVM (optional):**
- `cast` (Foundry) — for `cast disassemble`, `cast 4byte-decode`, reading storage
- `heimdall` (optional) — advanced EVM decompiler
- A block explorer API key (Etherscan, Arbiscan, etc.) for fetching verified source

## Workflow

### Phase 1: Recon

Gather the target contract(s):

```bash
# Solana — dump deployed program binary
solana program dump <PROGRAM_ID> program.so -u m

# Solana — check if IDL is published on-chain
anchor idl fetch <PROGRAM_ID> --provider.cluster mainnet -o idl.json

# EVM — fetch verified source (if available)
cast etherscan-source <ADDRESS> --chain <CHAIN> -d ./source

# EVM — get raw bytecode
cast code <ADDRESS> --rpc-url <RPC> > bytecode.hex
```

### Phase 2: Instruction Discovery (Solana)

#### Method 1: String Extraction (fastest, Anchor programs)

Anchor programs embed `"Instruction: <PascalCaseName>"` log strings in `.rodata`:

```bash
strings program.so | grep "^Instruction:" | sort -u
```

This recovers instruction names without source code or IDL.

#### Method 2: Discriminator Computation

Convert discovered PascalCase names to snake_case and compute Anchor discriminators:

```python
import hashlib

def anchor_discriminator(name: str) -> bytes:
    """Compute Anchor instruction discriminator: sha256('global:<snake_case>')[..8]"""
    return hashlib.sha256(f"global:{name}".encode()).digest()[:8]

def anchor_account_discriminator(name: str) -> bytes:
    """Compute Anchor account discriminator: sha256('account:<PascalCase>')[..8]"""
    return hashlib.sha256(f"account:{name}".encode()).digest()[:8]

# Example
name = "deposit_reserve_liquidity"
disc = anchor_discriminator(name)
print(f"{name}: {disc.hex()} = {list(disc)}")
```

#### Method 3: .rodata Analysis

Extract all string literals from the binary to find PDA seeds, error messages, and account names:

```bash
# Dump .rodata section
objdump -s -j .rodata program.so | head -200

# Extract all printable strings (min length 6)
strings -n 6 program.so | sort -u > strings.txt

# Find PDA seed candidates
grep -E "^[a-z_]{4,}" strings.txt

# Find error messages
grep -iE "error|invalid|overflow|unauthorized|insufficient" strings.txt
```

#### Method 4: Full IDL Recovery (if on-chain)

```bash
# Anchor programs may store IDL at PDA ["anchor:idl", program_id]
anchor idl fetch <PROGRAM_ID> --provider.cluster mainnet -o idl.json

# Parse the IDL
cat idl.json | python3 -m json.tool | head -100

# List all instructions
cat idl.json | python3 -c "
import json, sys
idl = json.load(sys.stdin)
for ix in idl.get('instructions', []):
    args = ', '.join(f\"{a['name']}: {a['type']}\" for a in ix.get('args', []))
    print(f\"  {ix['name']}({args})\")
"
```

### Phase 3: Account Structure Discovery (Solana)

```bash
# Dump a live account and inspect its data
solana account <ACCOUNT_ADDRESS> --output json -u m > account.json

# Extract discriminator (first 8 bytes of data)
python3 -c "
import json, base64
data = base64.b64decode(json.load(open('account.json'))['data'][0])
print(f'Discriminator: {data[:8].hex()} = {list(data[:8])}')
print(f'Total size: {len(data)} bytes')
print(f'Owner: ', json.load(open('account.json'))['owner'])
"

# If you have the IDL, decode the account
# Match discriminator against sha256("account:<TypeName>")[..8]
```

### Phase 4: Function Discovery (EVM)

```bash
# Disassemble bytecode
cast disassemble <ADDRESS> --rpc-url <RPC>

# Extract function selectors from bytecode (first 4 bytes of keccak256)
cast selectors $(cast code <ADDRESS> --rpc-url <RPC>)

# Reverse-lookup selectors via 4byte.directory
cast 4byte <SELECTOR>

# If Foundry not available, use the selector database directly
curl "https://www.4byte.directory/api/v1/signatures/?hex_signature=<SELECTOR>"

# Full decompilation (requires heimdall)
heimdall decompile <ADDRESS> --rpc-url <RPC> -o ./decompiled
```

### Phase 5: Cross-Reference & Audit

Once you have instruction names and account structures:

1. **Map the attack surface**: list all state-changing instructions, their signers, and account constraints
2. **Identify privileged operations**: look for admin/authority/owner patterns
3. **Check for missing validations**: compare declared accounts against actual usage
4. **Cross-reference with source** (if available): verify deployed binary matches published source

```bash
# Verify Solana program matches source (if anchor project)
anchor build
shasum -a 256 target/deploy/program.so
# Compare against: solana program dump <ID> deployed.so && shasum -a 256 deployed.so

# Verify EVM contract matches source
cast etherscan-source <ADDRESS> --chain mainnet -d ./verified-source
# Or use solana-verify for Solana programs
```

## Quick Reference: Solana Discriminator Formats

| Type | Format | Example |
|------|--------|---------|
| Anchor instruction | `sha256("global:<snake_case>")[..8]` | `global:initialize` |
| Anchor account | `sha256("account:<PascalCase>")[..8]` | `account:Vault` |
| SPL Token | `u8` enum index (0-25) | `0 = InitializeMint` |
| System Program | `u32` LE instruction index | `0 = CreateAccount` |
| Native (custom) | Program-specific, no standard | Varies |

## Integration with Audit Skills

After decoding, use the existing audit skills for systematic vulnerability analysis:

- **`/solana-security-audit`** — 35 attack vectors across Anchor, native Rust, and Pinocchio
- **`/solana-best-practices`** — 31 vulnerability patterns + case studies + Token-2022 security
- **`/evm-contract-audit`** — 120 real vulnerabilities from Code4rena
