#!/bin/sh

VERBOSE=0
OUTPUT=npm-manifest-check-results
for arg in $@
do
  case $arg in
    -h)
      echo """
***
Usage: check_and_output_packages.sh [<name>] [--verbose]
***
"""
      exit 0 ;;
    --verbose*) VERBOSE=1;;
    *)
      OUTPUT=$arg;;
  esac
done

RESULTS_ERRORS=""
RESULTS_TEXT=""
RESULTS_HTML="<html><head><style>*{font-family:Arial, sans-serif}table{border-collapse:collapse}td,th{padding:8px}.good{background-color:#00531f;color:rgb(132, 251, 151)}.bad{background-color:#930100;color:rgb(255, 218, 212)}tr{border:1px solid #8b9389}</style></head><body><table><thead><tr><th>Package</th><th>Output</th></tr></thead><tbody>"
RESULTS_JSON="["

while IFS= read -r pkg; do
  if [ $VERBOSE == 1 ]; then
    echo "Running for ${pkg}"
  fi
  PKG_RESULT="$(python3 npm-manifest-check.py "$pkg" --brief)";

  if [ $VERBOSE == 1 ]; then
    echo "${PKG_RESULT}"
  fi

# ERRORS
  case $PKG_RESULT in
    *"No mismatch detected for"*) RESULTS_ERRORS="${RESULTS_ERRORS}";;
    *) RESULTS_ERRORS="${RESULTS_ERRORS}${pkg}"$'\n\r';;
  esac

# TEXT
  CONCLUSION=" (ERROR)"
  case $PKG_RESULT in
    *"No mismatch detected for"*) CONCLUSION="";;
  esac
  RESULTS_TEXT="${RESULTS_TEXT}${pkg}${CONCLUSION}: ${PKG_RESULT}"$'\n\r'

# HTML
  CLASSNAME=bad
  case $PKG_RESULT in
    *"No mismatch detected for"*) CLASSNAME=good;;
  esac
  RESULTS_HTML="${RESULTS_HTML}<tr class=\"${CLASSNAME}\"><td>${pkg}</td><td>${PKG_RESULT//\!/!<br>}</td></tr>"

# JSON
  case $PKG_RESULT in
      *"No mismatch detected for"*) RESULTS_JSON="${RESULTS_JSON}{\"success\":true,\"pkg\":\"${pkg}\",\"output\":\"${PKG_RESULT}\"},";;
      *)
        RESULTS_JSON="${RESULTS_JSON}{\"success\":false,\"pkg\":\"${pkg}\",\"output\":["

        oIFS="$IFS"; IFS='!' # split on .
        set -o noglob     # disable glob
        set -- $PKG_RESULT"" # split+glob with glob disable
        IFS="$oIFS"
        for LINE in "$@"
        do
          RESULTS_JSON="${RESULTS_JSON}\"${LINE}\","
        done
        RESULTS_JSON="${RESULTS_JSON%,}]},"
      ;;
    esac
done < packages.list

RESULTS_HTML="${RESULTS_HTML}</tbody></table></body></html>"
RESULTS_JSON="${RESULTS_JSON%,}]"

echo $RESULTS_ERRORS > "${OUTPUT}-errors.txt"
echo $RESULTS_TEXT > "${OUTPUT}.txt"
echo $RESULTS_HTML > "${OUTPUT}.html"
echo $RESULTS_JSON > "${OUTPUT}.json"
