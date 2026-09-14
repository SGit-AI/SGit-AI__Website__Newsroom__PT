# 20 — The editor's review session

Run by the human editor of record (or by a Claude session the editor is driving), not on a
schedule. The message:

```
Run /newsroom-review. I am the editor of record. Show me each story in estado: verificado, one at
a time, with every claim beside the frozen source it stands on and its verification status. I will
say publish, hold, or send back with a note. Only set estado: publicado on my word. Then build,
run the gates, bump the version and push main.
```

The skill also handles two other things only the editor may do: a removal request under the
notice (`/newsroom-review removal <person-id>` — the entry is removed from derived data and every
page, the frozen snapshot is not altered, a decision file is written, no reason is recorded), and
clearing a `parado` issue.
