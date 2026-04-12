---
title: Migrating Obsidian digital gardens from Obsidian Publish to Quartz
tags:
  - knowledge-management
  - digital-garden
  - obsidian
  - quartz
  - how-to
status: seedling
---

# Migrating Obsidian digital gardens from Obsidian Publish to Quartz

I had two Obsidian-based digital gardens which I was pushing via Obsidian Publish. Wanted to move to [Quartz](https://quartz.jzhao.xyz), a free, open-source static site generator. The motivation, the steps, and the key fixes are all here, in enough detail to reproduce this for any similar setup.

Obsidian Publish is a paid service that makes publishing an Obsidian vault convenient. However it has a limitation: it delivers near-empty HTML shells to search engine crawlers. All page content is injected by JavaScript after the initial HTML loads. So Google/other crawls were pretty poor - AI bots too were not able to crawl properly. The practical result: pages submitted in a sitemap are not indexed, and a `site:yourdomain.com` search returns almost nothing even months after launch. The sidebar navigation in Obsidian Publish is also rendered via JavaScript, so Google cannot follow links from it to discover other pages.

Quartz is a static site generator. It builds every page into complete, standalone HTML at build time. When Google crawls any page, it receives the full content immediately, with no JavaScript rendering required. 
## Prerequisites

- Linux/macOS (this guide uses macOS-specific paths; Linux is equivalent, Windows differs)
- [Node.js](https://nodejs.org) v22 or higher
- npm v10.9 or higher
- Git
- A [GitHub](https://github.com) account
- A [Cloudflare](https://cloudflare.com) account (free tier sufficient)
- Your domain managed via Cloudflare DNS (mine was)

Check your versions:

```bash
node --version
npm --version
git --version
```

## Step 1 -- Clone and initialise Quartz

Quartz is forked from the upstream repository. For each site you want to publish, clone it into a local folder:

```bash
mkdir -p ~/Sites
cd ~/Sites
git clone https://github.com/jackyzha0/quartz.git your-site-name
cd your-site-name
npm i
npx quartz create
```

When prompted:
- **Initialise content folder**: choose `Empty Quartz`
- **Link resolution**: choose `Shortest path` (matches Obsidian's wikilink behaviour)

## Step 2 -- Configure the site

Edit `quartz.config.ts` and update two fields:

```ts
pageTitle: "Your Site Title",
baseUrl: "yourdomain.com",
```

## Step 3 -- Sync your vault content

Use `rsync` rather than `cp` to copy your vault into Quartz's `content/` folder. `rsync` handles exclusions cleanly and only transfers changed files on subsequent runs. in my case there were some stuff that needed to be excluded frmo the quartz deployment - some scripts i was running to render my publications and such. 

```bash
rsync -av --delete \
  --exclude='.git/' \
  --exclude='.obsidian/' \
  --exclude='Templates/' \
  --exclude='scripts/' \
  --exclude='_generated/' \
  --exclude='publish.css' \
  "/path/to/your/obsidian/vault/" \
  ~/Sites/your-site-name/content/
```

The `--delete` flag ensures files removed from your vault are also removed from the published site.

## Step 4 -- Create an index.md homepage

Quartz requires an `index.md` at the root of your content folder to serve as the homepage. Create this file inside your Obsidian vault itself (not just in the Quartz folder) so it survives future syncs. Forgot this and broke my quartz style and took a while to figure!

```markdown
---
title: Your Site Title
---

Your homepage content here.
```

## Step 5 -- Push to GitHub

Connect your local Quartz folder to a new GitHub repository:

```bash
cd ~/Sites/your-site-name
git remote set-url origin https://github.com/yourusername/your-repo-name.git
git add .
git commit -m "Initial Quartz setup"
git push -u origin v4
```

Note: Quartz's default branch is `v4`, not `main`.

When prompted for GitHub credentials, use a Personal Access Token (not your password). Generate one at GitHub > Settings > Developer settings > Personal access tokens > Tokens (classic). Tick the `repo` and `workflow` scopes.

## Step 6 -- Deploy on Cloudflare Pages

In the Cloudflare dashboard:

1. Workers & Pages > Create application > Pages > Connect to Git
2. Select your repository
3. Use these build settings:
   - **Build command**: `npx quartz build`
   - **Build output directory**: `public`
   - **Production branch**: `v4`
   - **Deploy command**: leave empty

Click Deploy. The first build takes 2-3 minutes.

## Step 7 -- Point your custom domain

In Cloudflare Pages, go to your project > Custom domains > Set up a custom domain. Enter your subdomain (e.g. `notes.yourdomain.com`). Cloudflare will detect any existing DNS record and offer to update it automatically. Confirm.

## Customisations

### Remove numbers from folder names in the sidebar

If your Obsidian vault uses numbered folders for sort ordering (e.g. `1. Areas`, `2. Projects`), Quartz will display these numbers in the sidebar, breadcrumbs, and folder page titles. Strip them at the display layer only -- your vault structure is untouched.

In `quartz.layout.ts`, replace `Component.Explorer()` with:

```ts
Component.Explorer({
  mapFn: (node) => {
    node.displayName = node.displayName.replace(/^\d+\.\s*/, "")
    return node
  },
}),
```

In `quartz/components/Breadcrumbs.tsx`, find the `formatCrumb` function and update it:

```ts
function formatCrumb(displayName: string, baseSlug: FullSlug, currentSlug: SimpleSlug): CrumbData {
  return {
    displayName: displayName.replaceAll("-", " ").replace(/^\d+\.\s*/, ""),
    path: resolveRelative(baseSlug, currentSlug),
  }
}
```

In `quartz/components/ArticleTitle.tsx`, strip numbers from page titles:

```ts
const raw = fileData.frontmatter?.title
const title = raw?.replace(/^\d+\.\s*-?\s*/, "")
```

In `quartz/plugins/emitters/folderPage.tsx`, find line 74 and replace the title generation:

```ts
title: folder.replace(/^\d+\.\s*-?\s*/, ""),
```

In `quartz/i18n/locales/en-US.ts`, set the folder label to empty so folder pages do not show a "Folder:" prefix:

```ts
folder: "",
```

### Custom footer

Replace `quartz/components/Footer.tsx` with a custom version. The SCSS file at `quartz/components/styles/footer.scss` controls styling -- italic text, a top border, and reduced opacity work well for a colophon-style footer:

```scss
footer {
  text-align: left;
  margin-bottom: 4rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--lightgray);

  p {
    font-style: italic;
    font-size: 0.85em;
    opacity: 0.75;
    line-height: 1.6;
    margin-bottom: 0.5rem;

    a {
      opacity: 0.85;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
  }
}
```

## The publish workflow

Create a shell script at the root of your Quartz folder. note exclusions if applicable. 

```bash
#!/bin/bash

echo "🌿 Syncing notes from Obsidian vault..."
rsync -av --delete \
  --exclude='.git/' \
  --exclude='.obsidian/' \
  --exclude='Templates/' \
  --exclude='scripts/' \
  --exclude='_generated/' \
  --exclude='publish.css' \
  "/path/to/your/obsidian/vault/" \
  ~/Sites/your-site-name/content/

echo "📦 Staging changes..."
cd ~/Sites/your-site-name
git add .

echo "💬 Committing..."
TIMESTAMP=$(date "+%Y-%m-%d %H:%M")
git commit -m "Publish notes – $TIMESTAMP"

echo "🚀 Pushing to GitHub..."
git push origin v4

echo "✅ Done! Site will update in ~2 minutes."
```

Make it executable and add a shell alias:

```bash
chmod +x ~/Sites/your-site-name/publish.sh
echo 'alias publish-notes="~/Sites/your-site-name/publish.sh"' >> ~/.zshrc
source ~/.zshrc
```

From then on, the entire publishing workflow is:

*publish-notes*

Cloudflare detects the push to GitHub and rebuilds the site automatically. Pages are live within approximately two minutes.

## Ongoing notes

- Obsidian remains the writing tool throughout. The vault structure, wikilinks, frontmatter, and tags all carry over to Quartz without modification.
- Folder numbers in Obsidian are useful for sort ordering within the app. They are stripped at display time by Quartz and do not appear on the website.
- If you rename a folder, the URL changes. Any external links to old URLs will break. Internal wikilinks are resolved by filename, not path, so they are unaffected by folder renames.
- The `--delete` flag in rsync means that deleting a note from Obsidian and then running the publish script will also remove it from the public site.
- Private folders can be excluded by adding them to the `--exclude` list in the publish script and to `ignorePatterns` in `quartz.config.ts`.

## Tools used

- [Quartz](https://quartz.jzhao.xyz) -- static site generator
- [Obsidian](https://obsidian.md) -- authoring tool
- [GitHub](https://github.com) -- version control and build trigger
- [Cloudflare Pages](https://pages.cloudflare.com) -- hosting and deployment
- [Google Search Console](https://search.google.com/search-console) -- indexing management

Last updated: 2026-04-12 11:28