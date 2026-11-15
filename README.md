# Paws Gone Wild — free video maker

This starter combines five **JPG** images into a silent 25-second vertical (1080 × 1920) MP4, with captions and a gentle zoom on each image.

## Setup

1. Upload `make_video.py` and `.github/workflows/create-short.yml` to your private GitHub repository, preserving folder paths.
2. Create an `images` folder and upload five JPG files named exactly `scene1.jpg`, `scene2.jpg`, `scene3.jpg`, `scene4.jpg`, and `scene5.jpg`, in story order.
3. In GitHub, select **Actions → Create Paws Gone Wild Short → Run workflow**.
4. When it finishes, open the workflow run and download the `paws-gone-wild-short` artifact. Extract the ZIP to find your MP4.

## Important limitations

- The scheduled GitHub workflow uses the same five images each time until you change them. It does **not** create fresh AI pictures or publish to YouTube.
- The video is silent. Add licensed audio later or configure audio in a future version.
- GitHub's cron schedule `0 23 */2 * *` means every other **day-of-month**, which can produce irregular gaps across month boundaries. It runs at 23:00 UTC, not at a guaranteed Pacific time; scheduled runs may be delayed.
- If any image is missing, the run will fail with a clear error.
- Keep the repository private if the images or assets should not be public.
