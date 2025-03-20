#!/usr/bin/env bash

for file in locales/*/LC_MESSAGES/click.po; do
  locale=$(basename $(dirname $(dirname $file)))
  output_dir=src/click/$(dirname $file)
  mkdir --parents $output_dir
  echo "Building .mo file for ${locale}"
  msgfmt --statistics --check-format $file -o $output_dir/click.mo
done
