for f in \
  "./talento_READY_2025-09-14.db.BAK."* \
  "./Makefile.bak" \
  "./ccp_vpm/templates/ccp_vpm/code_ghost.html.bak"
do
  [ -e "$f" ] && echo "ENCONTRADO: $f"
done
find . -type f \( -name '*.bak' -o -name '*.bak_*' -o -name '*.BAK' -o -name '*.BAK.*' -o -name '*.db.BAK.*' \) -print
