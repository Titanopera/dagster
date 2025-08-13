# AI Update PR summary

## Step 0: Always Inspect Repository State First

**CRITICAL**: It is essential to disregard any context about what branch you think you are on. ALWAYS start by inspecting the current state of the repository and GT stack to determine where you actually are.

**NEVER assume** you know the current branch or stack position based on previous context or conversation history. The repository state may have changed.

**Required commands to run first**:

**Sequential (must be run in order):**

1. `gt squash` - Squash commits in the current branch for cleaner history
2. `gt restack` - Ensure the stack is properly synced and up-to-date

**Parallel (can be run together):**

- `git branch --show-current` - Get the actual current branch name
- `gt ls -s` - Get the actual current stack structure
- `git status` - Verify repository state

**Important**: Run `gt squash` first, then `gt restack` (sequentially), as `gt restack` depends on the result of `gt squash`. The remaining commands can be run in parallel.

Only after confirming the actual repository state should you proceed with the remaining steps.

## Step 1: Identify the Previous Branch

First, use `gt ls -s` to view the stack structure. The output shows branches in order, with `◉` marking the current branch and `◯` marking other branches in the stack.

**CRITICAL**: The previous branch is the one that appears immediately AFTER the `◉` (current branch) in the `gt ls -s` output.

Example:

```
◉  feature/current-branch     <- Current branch (HEAD)
◯  feature/previous-branch    <- This is the previous branch to use
◯  feature/older-branch       <- NOT this one
◯  master
```

In this example, you would use `feature/previous-branch` as the `<previous_branch>`.

## Step 2: Get Changes for Current Branch Only

**CRITICAL**: Use the correct method to get changes for just the current branch:

1. **First, try `git log --oneline <previous_branch>..HEAD`** to see how many commits are in the current branch
2. **If there's only 1 commit**: Use `git diff HEAD~1..HEAD` to see the exact changes for that commit
3. **If there are multiple commits**: Use `git diff <previous_branch>..HEAD` where `<previous_branch>` is from Step 1

**Verification**: The `git log --oneline <previous_branch>..HEAD` command should typically show only 1-2 commits for the current branch. If it shows many commits, double-check that you identified the correct previous branch.

**Common Mistake**: Do NOT use `git diff <previous_branch>..HEAD` if it shows changes from multiple branches in the stack. Always verify you're looking at changes for just the current branch by checking the commit count first.

## Step 3: Write PR Summary

Focus only on changes in the current branch, not the entire stack history. Use this context, alongside any session context from what you know about the changes to write a PR summary in Markdown, of the format

```md
## Summary & Motivation

[Brief summary of changes here, including code sample, if a new API was added, etc.]

## How I Tested These Changes

[Very brief summary of test plan here, e.g. "New unit tests.", "New integration tests.", "Existing test suite." This can be a single sentence.]

## Changelog

[End user facing changelog entry, remove this section if no public-facing API was changed and no bug was fixed. Public-facing APIs are identified by the @public decorator. Ignore minor changes. If there are no user-facing changes, remove this section.]
```

Use bullet points sparingly, and do not overuse italics/bold text. Use short sentences.

After generating the PR summary markdown, check if there is a current PR for this branch using `gh pr view` or similar command. If there is no PR, error and tell the user to create a PR first. If there is a PR, update it with the generated summary using `gh pr edit --body "generated_summary_with_timestamp"` and also generate a concise, descriptive title based on the summary content and update it using `gh pr edit --title "generated_title"` or similar GitHub CLI command.

**Important**: Before updating the PR body, first get the current date with `date` command, then append the timestamp at the end of the PR body:

```
---
*Summary updated on [actual date from date command]*
```

Additionally, update the latest commit message in the branch with the contents of the PR summary using `git commit --amend -m "new_commit_message"` where the new commit message is derived from the PR summary title and content.
