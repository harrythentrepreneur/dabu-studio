# Express Builder Frontend Integration

## Overview

This document outlines the integration between the Express Builder frontend and the RunPod backend service. The backend is now hosted in a separate repository at ./backend for RunPod deployment.

## Key Changes Made

### 1. Frontend Updates (`frontend/app/(toolkit)/express-builder/page.tsx`)

#### New State Variables

- Added `processingMode` state to toggle between "express_builder" and "quick_create" modes
- Updated `ProcessingResult` interface to include new file types:
  - `captionedVideoUrl`
  - `projectBundleUrl`
  - `processingMode`
  - `capcutSuccess`

#### UI Enhancements

- Added processing mode toggle with two options:
  - **Express Builder Only**: Traditional video processing pipeline
  - **Quick Create + Captions**: Video processing + automatic caption generation
- Added informational tooltip explaining what Quick Create mode does
- Updated step count display to show 14 steps for Quick Create vs 10 for Express Builder only

#### API Integration Updates

- Modified `handleProcess` function to include new parameters:
  - `apply_captions`: Set to "true" for Quick Create mode
  - `caption_template`: Set to "1" (default template)
- Updated `handleStatusUpdate` to handle new response structure
- Enhanced result handling to include CapCut outputs

### 2. Processing Status Component Updates (`frontend/components/processing-status.tsx`)

#### New Props

- Added `isQuickCreate` prop to determine step configuration
- Updated step selection logic to use Quick Create steps when appropriate

#### Step Configuration

- **Express Builder Only**: 8-10 steps (depending on voiceover)
- **Quick Create**: 11-14 steps (including CapCut processing steps)

### 3. API Configuration Updates (`frontend/lib/api-config.ts`)

#### New Endpoints

- Added `downloadCaptionedVideo` for captioned video downloads
- Added `downloadProjectBundle` for CapCut project bundle downloads

### 4. Backend Updates (`backend/app.py`)

#### Enhanced Process Endpoint

- Updated to handle integrated Express Builder + Intelligent CapCut workflow
- Added proper status updates for all 14 steps
- Enhanced response structure to include CapCut outputs
- Improved error handling for partial failures

#### New Response Fields

- `captioned_video_path`: Path to video with captions
- `project_bundle_path`: Path to CapCut project bundle
- `processing_mode`: Indicates which processing path was used
- `capcut_success`: Boolean indicating CapCut processing success

### 5. Request Handlers Updates (`backend/api/request_handlers.py`)

#### Download Handler

- Added support for new file types:
  - `captioned_video`: Video with generated captions
  - `project_bundle`: CapCut project files
- Enhanced file discovery logic for CapCut outputs

#### Status Handler

- Updated to include new file types in status responses
- Enhanced download URL generation for CapCut outputs

## Workflow Integration

### Express Builder Only Mode (10 steps)

1. Loading inputs
2. Merging videos
3. Uploading to AI
4. AI Analysis
5. Validating duration
6. Extracting segments
7. Exporting outputs
8. Adding voiceover (if applicable)
9. Cleanup
10. Finalization

### Quick Create Mode (14 steps)

1. Loading inputs
2. Merging videos
3. Uploading to AI
4. AI Analysis
5. Validating duration
6. Extracting segments
7. Exporting outputs
8. Adding voiceover (if applicable)
9. Cleanup
10. Finalization
11. **Starting Intelligent CapCut processing**
12. **Uploading video to CapCut Web**
13. **Generating captions with selected style**
14. **Finalizing video with captions**

## File Types Supported

### Express Builder Outputs

- `video`: Final compiled video
- `script`: Processed script file
- `timestamps`: AI-generated timestamps
- `merged_full`: Full quality merged video

### Quick Create Additional Outputs

- `captioned_video`: Video with generated captions
- `project_bundle`: CapCut project files (ZIP)

## User Experience

### Mode Selection

- Users can toggle between processing modes before starting
- Clear visual indication of what each mode does
- Informational tooltips explain the differences

### Progress Tracking

- Real-time updates for all processing steps
- Different step counts based on selected mode
- Clear progress indicators for each phase

### Results Display

- Enhanced results show all available file types
- Download links for both Express Builder and CapCut outputs
- Processing mode and success status clearly displayed

## Error Handling

### Graceful Degradation

- If CapCut processing fails, Express Builder results are still available
- Clear error messages for each processing phase
- Partial success handling with detailed status

### Status Updates

- Real-time error reporting via SSE
- Step-by-step failure identification
- Recovery options for failed processes

## Testing

### Frontend Testing

- Test both processing modes
- Verify step progression
- Check result display for all file types
- Test error scenarios

### Backend Testing

- Verify API endpoint responses
- Test file generation and download
- Validate SSE status updates
- Check error handling

## Future Enhancements

### Potential Improvements

1. **Caption Style Selection**: Allow users to choose caption templates
2. **Batch Processing**: Support multiple video processing
3. **Template Management**: Save and reuse caption styles
4. **Progress Persistence**: Resume interrupted processing
5. **Quality Settings**: Adjust video quality and caption parameters

### Integration Opportunities

1. **Analytics Dashboard**: Track processing success rates
2. **User Preferences**: Remember preferred processing modes
3. **Template Library**: Community-shared caption styles
4. **Export Options**: Multiple output formats and resolutions

## Technical Notes

### Dependencies

- Frontend: React, TypeScript, Tailwind CSS
- Backend: Python, Flask, Playwright, Gemini Vision
- Communication: Server-Sent Events (SSE), REST API

### Performance Considerations

- SSE connection management
- File upload/download optimization
- Browser automation reliability
- Error recovery mechanisms

### Security

- File type validation
- Request ID generation
- Temporary file cleanup
- API endpoint protection

---

_Document created: August 17, 2025_  
_Status: Integration Complete - Ready for Testing_
