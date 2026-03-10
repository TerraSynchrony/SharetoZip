# Phone-only GitHub deployment

This repo bundle is set up so GitHub Actions builds the APK for you in the cloud.

## What to upload to a new GitHub repo
Upload the contents of this bundle so the repo contains:

- `.github/workflows/build-apk.yml`
- `android_share_zip_mvp/main.py`
- `android_share_zip_mvp/buildozer.spec`
- `android_share_zip_mvp/intent_filters.xml`
- `android_share_zip_mvp/README.md`

## Fastest mobile workflow
1. Create a new empty GitHub repo in your phone browser.
2. Upload the `android_share_zip_mvp` folder contents to the repo.
3. Create the workflow file at `.github/workflows/build-apk.yml` using the file from this bundle.
4. Open the repo's **Actions** tab.
5. Run **Build APK**.
6. After the workflow finishes, open the run and download the `sharetozip-apk` artifact.
7. Install the APK on Android when prompted.
8. Share multiple files into the app and check **Downloads** for the generated ZIP.

## Important note
GitHub's mobile web UI can be awkward with nested folders. If your browser/file picker cannot preserve the `.github/workflows` path, create that file directly in GitHub's web editor and upload only the `android_share_zip_mvp` folder files.
