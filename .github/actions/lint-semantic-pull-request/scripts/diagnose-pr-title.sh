#!/bin/bash
set -euo pipefail

PR_TITLE="$1"
HEADER_PATTERN="$2"

if perl -e "exit(!(\$ARGV[0] =~ m/$HEADER_PATTERN/))" "$PR_TITLE" 2>/dev/null; then
  exit 0
fi

if ! echo "$PR_TITLE" | grep -q ': '; then
  echo "Missing \`: \` (colon + space) separator."
  echo ""
  echo "Expected format: \`type(scope): description\` or \`type: description\`"
  exit 0
fi

TYPE_SCOPE="${PR_TITLE%%: *}"
SUBJECT="${PR_TITLE#*: }"

if [ -z "$SUBJECT" ]; then
  echo "Missing description after \`: \`."
  exit 0
fi

if [[ "$TYPE_SCOPE" =~ \( ]] && ! [[ "$TYPE_SCOPE" =~ \)$ ]]; then
  echo "Unclosed parenthesis in scope."
  echo ""
  echo "Expected format: \`type(scope): description\`"
  exit 0
fi

if [[ "$TYPE_SCOPE" =~ ^([a-zA-Z]+)\((.*)\)$ ]]; then
  SCOPE="${BASH_REMATCH[2]}"
elif [[ "$TYPE_SCOPE" =~ ^([a-zA-Z]+)$ ]]; then
  SCOPE=""
else
  echo "Could not parse type from: \`$TYPE_SCOPE\`."
  echo ""
  echo "Type must be letters only, e.g. \`feat\`, \`fix\`, \`ci\`."
  exit 0
fi

if [ -n "$SCOPE" ]; then
  INVALID=$(echo "$SCOPE" | sed 's/[a-zA-Z0-9_$.*/ ,:-]//g')
  if [ -n "$INVALID" ]; then
    UNIQUE=$(echo "$INVALID" | fold -w1 | sort -u | tr '\n' ' ' | sed 's/ $//')
    echo "Scope \`($SCOPE)\` contains invalid character(s): \`$UNIQUE\`"
    echo ""
    echo "Allowed in scope: letters, digits, \`_\` \`$\` \`.\` \`-\` \`*\` \`/\` \`,\` and spaces."
    exit 0
  fi
fi

echo ""
