# Xampler experience assessment

## Red-green-refactor TDD support

Xampler is now reasonably supportive of red-green-refactor TDD for library APIs:

- **Red**: add a unit test against a fake binding or `Demo*` transport in `tests/`.
- **Green**: implement the small wrapper in `xampler/`.
- **Refactor**: update one executable example to import the wrapper and run local verification.

Strongest TDD surfaces today: R2, D1, KV, Queues, Vectorize, Workers AI, Workflows, Durable Object refs, Cron, AI Gateway demo shapes, response helpers.

Weak spots remain where realism needs account resources: Hyperdrive, Browser Rendering, R2 Data Catalog append/read, Agents SDK interop, and advanced Durable Object/WebSocket hibernation semantics.

## Impact of `xc`

`xc` makes the complete Xampler experience less verbose and easier to explain:

```bash
xc doctor
xc verify r2
xc remote prepare vectorize
xc remote verify vectorize
xc remote cleanup vectorize
```

Before `xc`, the user had to remember repo-internal script paths and opt-in env gates. After `xc`, the verbs map to the mental model: doctor, verify, remote prepare/verify/cleanup, dev link/restore.

Impact:

| Dimension | Impact |
|---|---|
| Verboseness | Lower: common script invocations collapse to short verbs. |
| Understandability | Higher: the CLI exposes the lifecycle vocabulary directly. |
| Competitiveness | Higher: Xampler now feels more like a library/product than a folder of examples. |
| Quality | Higher: `doctor` makes credentials/tool readiness inspectable before failure. |

`xc` does not replace direct examples or docs. It makes the learning path executable and repeatable.

## Remaining DX work

- Add `xc list` and `xc docs <surface>`.
- Add `xc new <surface>` scaffolding for low-cost examples.
- Have `xc doctor` recommend exact missing credentials per selected profile.
- Emit remote-cost warnings before prepare/deploy commands.
