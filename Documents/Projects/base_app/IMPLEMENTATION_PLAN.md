# Implementation Plan for Generic Page Settings

## Changes needed:

### Frontend (templates/index.html):
1. Replace integrationsSettingsOpen with generic pageSettingsOpen state that tracks which page
2. Replace integrationsForm with generic pageForm
3. Add generic uploadPageImage function
4. Add generic savePageSettings function  
5. Add generic handlePageImageResize function
6. Update action bar to show settings icon on all non-parent pages
7. Create generic page settings modal
8. Update page content display to show text/image for all pages

### Implementation:
- Use activeMenuId to determine which page settings to load/save
- Reuse same modal for all pages
- Store settings in settings.page_settings[page_id]
