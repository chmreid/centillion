# Secrets

## Summary

This repo requires the use of secrets for integration tests, which make
real API calls to real cloud services.

## Travis Secrets

We have an encrypted secrets file called `secrets.tar.gz` that contains
files useful for Travis integration tests.

Contents of `secrets.tar.gz`:

- `config/config.integration.json` - integration credentials, containing working OAuth keys
  for Google and Github and any other services

Instructions for encrypting/decrypting can be found in the Travis documentation here:

<https://docs.travis-ci.com/user/encrypting-files/#manual-encryption>

### Quick Start: Secrets with Travis

**Step 1: Encrypt Secret File**

To encrypt a file, pick a passphrase and use OpenSSL
to encrypt the file with that passphrase:

```
openssl aes-256-cbc -k "<your password>" -in secrets.tar.gz -out secrets.tar.gz.enc
```

**Step 2: Add password to repository's Travis settings.** 

Log in to Travis and navigate to the project. Modify the
settings of the repository. There is a section where you
can add environment variables.

Add a new environment variable named `credentials_password`
with the value of `<your password>` (same password used in
the above command).

Now you can add the following command in your
`.travis.yml` file to decrypt the secrets file:

```
before_install:
- ...
- cd tests/
- openssl aes-256-cbc -k "$credentials_password" -in secrets.tar.gz.enc -out secrets.tar.gz -d
- ...
```

Once you've added the encrypted secrets file 
(don't add the original, unencrypted secrets file!),
you can commit it along with the `.travis.yml` file,
and Travis should be able to access the secrets
using the secret password provided via the environment
variable.

