pip install --target ./package requests
pushd package
zip -r9 ${OLDPWD}/function.zip .
popd
zip -g function.zip airtable_tasks.py airtable.py

