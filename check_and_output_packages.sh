#!/bin/sh
pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

VERBOSE=0
FORMAT=json
OUTPUT=npm-manifest-check-result
for arg in $@
do
  case $arg in
    -h)
      echo """
***
Usage: check_and_output_packages.sh [<name>] [--format=json|html|text] [--verbose]
***
"""
      exit 0 ;;
    --verbose*) VERBOSE=1;;
    --format*)
      TMP_FORMAT=${arg:9}
      case $TMP_FORMAT in
        text) FORMAT=text;;
        html) FORMAT=html;;
        json) FORMAT=json;;
      esac;;
    *)
      OUTPUT=$arg;;
  esac
done
OUTPUT="${OUTPUT}.${FORMAT}"

RESULTS=""
if [ $FORMAT == "json" ]; then
  RESULTS="["
fi
if [ $FORMAT == "html" ]; then
  RESULTS="<html><head><style>*{font-family:Arial, sans-serif}table{border-collapse:collapse}td,th{padding:8px}.good{background-color:#00531f;color:rgb(132, 251, 151)}.bad{background-color:#930100;color:rgb(255, 218, 212)}tr{border:1px solid #8b9389}</style></head><body><table><thead><tr><th>Package</th><th>Output</th></tr></thead><tbody>"
fi

while IFS= read -r pkg; do

  pushd "$(dirname "$0")"
  PKG_RESULT="$(python3 npm-manifest-check.py "$pkg" --brief)";
  popd

  if [ $VERBOSE == 1 ]; then
    echo "${PKG_RESULT}"
  fi

  case $FORMAT in
    text)
      CONCLUSION=" (ERROR)"
      case $PKG_RESULT in
        "No mismatch detected for"*) CONCLUSION="";;
      esac
      RESULTS="${RESULTS}${pkg}${CONCLUSION}: ${PKG_RESULT}"$'\n\r'
    ;;
    html)
      CLASSNAME=bad
      case $PKG_RESULT in
        "No mismatch detected for"*) CLASSNAME=good;;
      esac
      RESULTS="${RESULTS}<tr class=\"${CLASSNAME}\"><td>${pkg}</td><td>${PKG_RESULT//\!/!<br>}</td></tr>"
    ;;

    json)
      case $PKG_RESULT in
          "No mismatch detected for"*) RESULTS="${RESULTS}{\"success\":true,\"pkg\":\"${pkg}\",\"output\":\"${PKG_RESULT}\"},";;
          *)
            RESULTS="${RESULTS}{\"success\":false,\"pkg\":\"${pkg}\",\"output\":["

            oIFS="$IFS"; IFS='!'
            set -f
            LINES=($PKG_RESULT)
            IFS="$oIFS"
            for LINE in "${LINES[@]}"
            do
              RESULTS="${RESULTS}\"${LINE}\","
            done
            RESULTS="${RESULTS%,}]},"
          ;;
        esac
  ;;
  esac
done < packages.list

if [ $FORMAT == "json" ]; then
  RESULTS="${RESULTS%,}]"
fi
if [ $FORMAT == "html" ]; then
  RESULTS="${RESULTS}</tbody></table></body></html>"
fi

echo $RESULTS > $OUTPUT
