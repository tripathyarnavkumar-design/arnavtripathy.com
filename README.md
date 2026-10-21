# arnavtripathy.com

Personal website of Arnav Kumar Tripathy. It's live at https://www.arnavtripathy.com once the domain is connected.

## Editing the website

Edit everything at **https://app.pagescms.org**. Sign in with GitHub and open this repository.

| To change… | Open in the admin |
|---|---|
| A project, or add a new one | **Design projects** → pick one, or **Add an entry** |
| Publications, presentations | **Research** |
| Courses and teaching roles | **Teaching** |
| Education, work, awards | **About** |
| Art pieces and their images | **Art & Craft** |
| Web tools | **Tools** |
| Home page text | **Home page** |
| Name, email, résumé PDF, profile links | **Site settings** |

Click **Save**. The site rebuilds and is live about a minute later. You can follow progress under the **Actions** tab of this repository.

**Images.** Upload them straight into an image field. JPG or PNG at most about 2000 px wide keeps pages fast.

**"To add" reminders.** Empty sections show a "To add" reminder on the site. When the content is ready to share, turn off **Show "To add" reminders** in **Site settings**, and every empty section is then hidden.

**New project.** In **Design projects**, add an entry. Fill in the title, position, categories and description, then add text sections and images. Its page, its card on the Design page and the previous/next links are all created automatically.

## How it is built (for bigger changes)

| Folder or file | Contains |
|---|---|
| `content/` | All text, as YAML; one file per project in `content/projects/` |
| `media/` | Uploaded images and files |
| `templates/` | Page layouts (Jinja2 HTML) |
| `assets/` | `styles.css`, `script.js` |
| `apps/` | Stand-alone web tools, each published at its own address, e.g. `apps/dataviz-now/` → www.arnavtripathy.com/dataviz-now/ |
| `build.py` | Turns the above into the finished site in `_site/`: `pip install -r requirements.txt && python3 build.py` |
| `.pages.yml` | The admin forms |
| `.github/workflows/deploy.yml` | Builds and publishes to GitHub Pages on every change |
