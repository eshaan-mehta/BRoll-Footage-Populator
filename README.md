# DaVinci Resolve B-Roll Generator

This is a Python script for DaVinci Resolve that automatically generates B-roll footage using clips from your Media Pool.

Designed to speed up the editing workflow, this tool allows editors to quickly create background visuals or montage layers without manually scrubbing through hours of footage.

## 🚀 Features

* **Native GUI:** Built with `tkinter`, requiring no external library installations.
* **Smart Media Filtering:** Automatically detects video and static image files while ignoring Timelines and Audio-only files to prevent errors.
* **Flexible Track Targeting:**
    * Create a **New Track** automatically.
    * Append to any **Existing Track** (excluding Track 1 to protect the A-Roll/Main Edit).
* **Intelligent Gap Filling:**
    * **Match Track 1:** Automatically calculates the duration of your main edit and fills the B-roll track to match.
    * **Fixed Duration:** Specify an exact length (e.g., 60 seconds) to generate.
    * **Smart Append:** If adding to an existing track, it detects the current end point and appends from there.
* **Randomization Engine:**
    * Selects random start points within source clips (random seeking).
    * Varies clip duration based on user-defined Min/Max bounds.
* **Safe Insertion:** Uses "Video Only" insertion logic to prevent audio track collisions and sync issues.

## 📋 Prerequisites

* **DaVinci Resolve** (Free or Studio version 16+).
* **Python 3.6+** (Usually pre-installed with DaVinci Resolve).

> **Note:** This script relies on the DaVinci Resolve Scripting API (`DaVinciResolveScript`). It must be run from *inside* Resolve to function correctly.

## 🛠️ Installation

1.  Download the `broll_generator.py` file from this repository.
2.  Move the file to the DaVinci Resolve **Utility Scripts** folder:

    * **Windows:**
        `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility\`
    * **macOS:**
        `/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Utility/`
    * **Linux:**
        `/opt/resolve/Fusion/Scripts/Utility/`

3.  Restart DaVinci Resolve.

## 📖 Usage

1.  Open your project in DaVinci Resolve and open the **Edit Page**.
2.  Go to the top menu bar: **Workspace** > **Scripts** > **broll_generator**.
3.  The GUI window will appear.

### Step-by-Step Workflow

1.  **Select Clips:** The window lists all valid video/image clips found in your Media Pool. Check the boxes next to the clips you want to include in the randomization pool.
    * *Tip: Use the "Select All" button for quick selection.*
2.  **Choose Destination:**
    * **New Track:** Creates a new Video and Audio track and places footage there.
    * **Track X:** Appends footage to the end of an existing track.
3.  **Configure Timing:**
    * **Min/Max Sec:** Determines how long each individual slice of video will be (e.g., between 2s and 5s).
    * **Target Duration:** Choose to match the length of your main edit (Track 1) or generate a specific amount of footage.
4.  **Generate:** Click **GENERATE B-ROLL TRACK**.

## ⚙️ How It Works (Under the Hood)

This script interacts with the Resolve API to perform operations that would be tedious by hand:

1.  **Scanning:** It recurses through the Media Pool folders to build a list of valid `MediaPoolItems`.
2.  **Calculation:** It determines the timeline's start timecode (handling timelines that start at `01:00:00:00`) and the target fill length.
3.  **The Loop:**
    * It picks a random clip from your selection.
    * It calculates a random duration (e.g., 3.5 seconds).
    * It performs a **Random Seek**: It looks at the source clip's total duration and calculates a random entry point (`StartFrame`), ensuring the slice fits within the file bounds.
4.  **Insertion:** It uses the `AppendToTimeline` API method with a constructed dictionary. Crucially, it sets `"mediaType": 1` (Video Only), which forces Resolve to ignore the source audio channels. This allows the script to place video clips onto the timeline even if the audio track configuration (Stereo vs. Mono) doesn't match, preventing API failures.

## ⚠️ Known Limitations

* **API Performance:** Large Media Pools (1000+ items) may take a moment to scan upon opening the script.
* **Static Images:** While images are supported, they cannot be "slipped" (random seek) as they have no timecode. The script simply resizes them to the requested duration.
* **Track 1 Protection:** The script intentionally disables selecting "Track 1" as a destination to prevent accidental overwriting of the main timeline.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
