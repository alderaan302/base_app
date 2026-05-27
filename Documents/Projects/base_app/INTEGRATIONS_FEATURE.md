# Integrations Feature

## Overview
Added comprehensive integration management system to the IBM Expert Labs application. Users can now upload, display, and manage integrations through a plugin-style architecture.

## Features Implemented

### 1. Integration Upload
- **Location**: Settings lightbox for Integrations page
- **File Type**: .tgz (tar gzip) archives
- **Validation**: Checks file extension before upload
- **Extraction**: Automatically extracts to `settings/integrations/{name}/`

### 2. Integration Structure
Each integration must contain:
```
integration-name/
├── metadata.json  # Contains name and description
└── icon.png       # Logo image (can also be .jpg or .jpeg)
```

**metadata.json format**:
```json
{
  "name": "Integration Name",
  "description": "Description of the integration"
}
```

### 3. Integration Display
- **Table View**: Displays all uploaded integrations in a styled table
- **Columns**:
  - Icon (left) - 32x32px image
  - Name
  - Description
  - Actions (right)
- **Styling**: Grey background (#393939) matching action bar theme
- **Empty State**: Shows "You have no integrations added yet" when no integrations exist

### 4. Integration Management
- **Delete**: Red trash icon in actions column with confirmation dialog
- **Auto-refresh**: Table updates automatically after upload or delete

## Backend API Endpoints

### GET /api/integrations
Lists all installed integrations
- **Response**: `{"integrations": [{id, name, description, icon}, ...]}`

### POST /api/integrations/upload
Upload and extract .tgz integration file
- **Request**: multipart/form-data with file
- **Validates**: .tgz extension
- **Extracts**: To integrations/{name}/
- **Checks**: Duplicate integration names

### DELETE /api/integrations/<id>
Remove integration and its folder
- **Request**: DELETE with integration ID
- **Action**: Deletes entire integration directory

### GET /integration-icon/<id>/<filename>
Serve integration icon files
- **Supports**: .png, .jpg, .jpeg

## Test Integration

A VirtualBox test integration is included:
- **File**: `VirtualBox.tgz`
- **Name**: VirtualBoxREST
- **Description**: An integration with A rest API to display devices
- **Icon**: Oracle VirtualBox logo (30KB PNG)

## Usage Instructions

### Installing the Test Integration
1. Navigate to Integrations page
2. Click Settings icon in action bar
3. Scroll to "Import integration" section
4. Click "Choose File"
5. Select `VirtualBox.tgz`
6. Integration appears in table automatically

### Creating Custom Integrations
1. Create directory with integration files:
   - `metadata.json` (required)
   - `icon.png` or `icon.jpg` (required)
2. Package as .tgz:
   ```bash
   tar -czf MyIntegration.tgz -C path/to/integration .
   ```
3. Upload through UI

### Deleting Integrations
1. Click trash icon in Actions column
2. Confirm deletion
3. Integration removed from table and filesystem

## Technical Details

### Storage Location
- **Path**: `settings/integrations/{integration_name}/`
- **Permissions**: Inherits from settings directory

### Frontend Components
- **State**: `integrations` array in React state
- **Icons**: TrashIcon component for delete
- **Modal**: Import section in page settings modal (integrations page only)
- **Table**: Custom CSS with hover effects

### Error Handling
- File type validation before upload
- Duplicate integration name detection
- Failed upload/delete error messages
- Missing metadata or icon handling

## CSS Classes
- `.integrations-table` - Main table styling
- `.integration-icon` - Icon image sizing
- `.empty-state` - No integrations message
- `.delete-icon-button` - Trash icon button with hover
