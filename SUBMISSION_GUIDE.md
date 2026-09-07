# RoadSense SIH 2026 Submission Guide

Use this checklist before sharing the RoadSense GitHub repository link.

## Required repository content

- Actual RoadSense source code is present.
- `README.md` explains the project clearly.
- PS ID and PS title are included.
- Problem statement and proposed solution are explained.
- Key features are listed.
- Technology stack is listed.
- Setup and run instructions are provided.
- Team members and roles are mentioned.
- Important screenshots and prototype outputs are included.
- Final PPT/PPTX is placed in `submission/` whenever practical.
- If the PPT is too large for GitHub, an accessible Google Drive/OneDrive viewer link is added to `submission/PRESENTATION.md`.
- Demo video link is added to `submission/DEMO.md` if available.
- Repository is accessible to reviewers.

## Recommended structure

ROAD-SENSE/
├── README.md
├── SUBMISSION_GUIDE.md
├── LICENSE
├── submission/
│   ├── PRESENTATION.md
│   └── DEMO.md
├── docs/
│   └── architecture.md
├── assets/
│   └── screenshots/
├── backend/
├── frontend/
└── yolo/

## Presentation

Upload the final PPT/PPTX to the `submission/` folder when the file size is suitable for GitHub.

Use a clear filename such as:

TENSORS_SIH2026_Presentation.pptx

If the PPT is too large, use Google Drive or OneDrive and put the shareable viewer link in `submission/PRESENTATION.md`.

## Demo video

The demo video is recommended for demonstrating the working RoadSense prototype.

If available, add its YouTube/Google Drive link to `submission/DEMO.md` and make sure it is accessible without requesting permission.

The demo should ideally show:

- Camera/video input
- AI accident and pothole detection
- Non Accident filtering
- 3-of-5 temporal confirmation
- Backend reporting
- Incident appearing on the dashboard
- GIS incident map
- Road Condition Intelligence
- Traffic / Fleet Analytics

## Screenshots / prototype outputs

Put important screenshots and prototype outputs in:

assets/screenshots/

Include useful final results rather than random development screenshots.

Recommended screenshots include:

- RoadSense dashboard
- AI detection output
- GIS incident map
- Road Condition Intelligence
- Traffic / Fleet Analytics
- Manual incident reporting
- Backend/database result if useful for demonstrating the working pipeline

## Do not upload

- Passwords
- API keys
- Access tokens
- `.env` files containing secrets
- Private credentials
- Other confidential information

## README should answer

- What problem are you solving?
- What is your proposed solution?
- How does RoadSense work?
- Which technologies did you use?
- How can a reviewer run it?
- What video input options are supported?
- What does the final output look like?
- What are the important features?
- What is the expected impact?

## Before submission

Open the repository in a private/incognito browser window or while logged out.

Verify that the reviewer can access:

- Source code
- `README.md`
- Architecture documentation
- PPT/presentation
- Screenshots
- Demo video
- Any external links that are supposed to be public

Also verify that no passwords, API keys, access tokens, `.env` files, or other private credentials have been committed.