import tkinter as tk
from tkinter import ttk, messagebox
import random
import re

# --- 1. CONNECT TO RESOLVE ---
try:
    resolve = app.GetResolve()
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    media_pool = project.GetMediaPool()
    
    timeline_fps = project.GetSetting("timelineFrameRate")
    FPS = float(timeline_fps) if timeline_fps else 24.0
    
except NameError:
    print("Error: 'app' not found. Please run this script INSIDE DaVinci Resolve.")
    resolve, project, media_pool = None, None, None
    FPS = 24.0

# --- HELPER: Timecode to Frames ---
def parse_timecode_to_frames(timecode_str):
    try:
        parts = re.split('[:;]', timecode_str)
        if len(parts) != 4: return 0
        h, m, s, f = map(int, parts)
        return int((h * 3600 + m * 60 + s) * FPS + f)
    except Exception:
        return 0

# --- MAIN LOGIC ---
class BRollGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("B-Roll Generator (Timecode Fix)")
        self.root.geometry("500x700")
        
        self.check_vars = [] 
        
        self.setup_ui()
        self.scan_media_pool()

    def log(self, message):
        """Prints to console and updates UI label"""
        print(f"[LOG] {message}")
        self.lbl_status.config(text=message)
        self.root.update()

    def setup_ui(self):
        # 1. Clip Selection Area
        lbl_list = tk.Label(self.root, text="1. Select Source Clips:", font=("Arial", 10, "bold"))
        lbl_list.pack(pady=(10, 5), anchor="w", padx=10)
        
        list_container = tk.Frame(self.root, bd=1, relief="sunken")
        list_container.pack(fill="both", expand=True, padx=10)
        
        self.canvas = tk.Canvas(list_container)
        self.scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Selection Tools
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(btn_frame, text="Select All", command=self.select_all).pack(side="left", padx=(0, 5))
        tk.Button(btn_frame, text="Select None", command=self.select_none).pack(side="left", padx=(0, 5))
        tk.Button(btn_frame, text="Refresh Clips", command=self.scan_media_pool).pack(side="left")
        self.lbl_count = tk.Label(btn_frame, text="Selected: 0", fg="blue", font=("Arial", 10, "bold"))
        self.lbl_count.pack(side="right")
        
        # 2. Settings Area
        lbl_settings = tk.Label(self.root, text="2. Configuration:", font=("Arial", 10, "bold"))
        lbl_settings.pack(pady=(15, 5), anchor="w", padx=10)
        
        frame_settings = tk.LabelFrame(self.root, text="Clip Settings")
        frame_settings.pack(fill="x", padx=10)
        
        # -- Track Selection (NEW) --
        tk.Label(frame_settings, text="Dest Track:").grid(row=0, column=0, padx=5, pady=5)
        self.track_var = tk.StringVar()
        self.combo_tracks = ttk.Combobox(frame_settings, textvariable=self.track_var, state="readonly", width=15)
        self.combo_tracks.grid(row=0, column=1, columnspan=2, sticky="w")
        
        # -- Min/Max --
        tk.Label(frame_settings, text="Min Sec:").grid(row=1, column=0, padx=5, pady=5)
        self.entry_min = tk.Entry(frame_settings, width=5)
        self.entry_min.insert(0, "2.0")
        self.entry_min.grid(row=1, column=1, sticky="w")
        
        tk.Label(frame_settings, text="Max Sec:").grid(row=1, column=2, padx=5, pady=5)
        self.entry_max = tk.Entry(frame_settings, width=5)
        self.entry_max.insert(0, "5.0")
        self.entry_max.grid(row=1, column=3, sticky="w")
        
        # 3. Track Duration
        frame_dur = tk.LabelFrame(self.root, text="Target Duration Logic")
        frame_dur.pack(fill="x", padx=10, pady=10)
        
        self.dur_mode = tk.StringVar(value="match")
        
        rb1 = tk.Radiobutton(frame_dur, text="Fill to Match Track 1 End", variable=self.dur_mode, value="match")
        rb1.pack(anchor="w")
        
        frame_manual = tk.Frame(frame_dur)
        frame_manual.pack(anchor="w")
        
        rb2 = tk.Radiobutton(frame_manual, text="Add Fixed Seconds:", variable=self.dur_mode, value="fixed")
        rb2.pack(side="left")
        
        self.entry_total = tk.Entry(frame_manual, width=8)
        self.entry_total.insert(0, "60")
        self.entry_total.pack(side="left", padx=5)

        # 4. Status Bar
        self.lbl_status = tk.Label(self.root, text="Ready", bd=1, relief="sunken", anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

        # 5. Generate Button
        self.btn_run = tk.Button(self.root, text="GENERATE B-ROLL", bg="white", font=("Arial", 11, "bold"),
                                    command=self.generate)
        self.btn_run.pack(fill="x", padx=20, pady=10, ipady=5)
        
    def update_count(self):
        count = sum(1 for var, _, _ in self.check_vars if var.get())
        total = len(self.check_vars)
        self.lbl_count.config(text=f"Selected: {count} / {total}")

    def select_all(self):
        for var, _, _ in self.check_vars: var.set(True)
        self.update_count()

    def select_none(self):
        for var, _, _ in self.check_vars: var.set(False)
        self.update_count()

    def scan_media_pool(self):
        if not media_pool: return

        self.log("Scanning Media Pool & Tracks...")
        
        # 1. Update Clips
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.check_vars = []
        root_folder = media_pool.GetRootFolder()
        
        def get_clips_recursive(folder):
            found = []
            clips = folder.GetClipList()
            for clip in clips:
                c_type = clip.GetClipProperty("Type")
                if "Timeline" in c_type: continue
                if "Video" in c_type or "Image" in c_type or "Stills" in c_type:
                    found.append((clip, folder))
            subfolders = folder.GetSubFolderList()
            for sub in subfolders:
                found.extend(get_clips_recursive(sub))
            return found

        all_clips = get_clips_recursive(root_folder)
        self.log(f"Found {len(all_clips)} clips.")
        
        if not all_clips:
            tk.Label(self.scrollable_frame, text="No Video Clips Found!").pack()
        else:
            for clip, folder in all_clips:
                var = tk.BooleanVar(value=False)
                chk = tk.Checkbutton(self.scrollable_frame, text=clip.GetName(), 
                                     variable=var, anchor="w", command=self.update_count)
                chk.pack(fill="x", padx=5, pady=2)
                self.check_vars.append((var, clip, folder))
        self.update_count()

        # 2. Update Tracks (Logic: New Track OR Existing Tracks except V1)
        try:
            timeline = project.GetCurrentTimeline()
            if timeline:
                track_count = timeline.GetTrackCount("video")
                # Options: "New Track", then "Track 2", "Track 3" ... (Skip 1)
                options = ["New Track"]
                for i in range(2, track_count + 1):
                    options.append(f"Track {i}")
                
                self.combo_tracks['values'] = options
                self.combo_tracks.current(0) # Default to New Track
        except Exception:
            self.combo_tracks['values'] = ["New Track"]
            self.combo_tracks.current(0)

    def generate(self):
        if not project:
            messagebox.showerror("Error", "Not connected to Resolve.")
            return

        timeline = project.GetCurrentTimeline()
        if not timeline:
            messagebox.showerror("Error", "Please open a timeline first.")
            return

        # --- Helper: Get End Frame of specific track ---
        def get_track_end_time(track_idx):
            items = timeline.GetItemListInTrack("video", track_idx)
            if not items: return timeline.GetStartFrame()
            return max([item.GetEnd() for item in items])

        # --- 1. Determine Destination Track & Start Point ---
        selection = self.track_var.get()
        dest_track_idx = 0
        current_timeline_pos = timeline.GetStartFrame()
        
        if selection == "New Track":
            timeline.AddTrack("video")
            timeline.AddTrack("audio") # Adding matched audio track as requested previously
            dest_track_idx = timeline.GetTrackCount("video")
            current_timeline_pos = timeline.GetStartFrame() # New Track starts at beginning of timeline
        else:
            try:
                # Parse "Track n" -> n
                dest_track_idx = int(selection.split(" ")[1])
                
                # Start adding from the END of this track
                current_timeline_pos = get_track_end_time(dest_track_idx)
            except:
                messagebox.showerror("Error", f"Invalid track selection: {selection}")
                return

        self.log(f"Targeting Video Track {dest_track_idx} starting at frame {current_timeline_pos}")

        # --- 2. Determine How Much To Fill ---
        frames_to_fill = 0
        if self.dur_mode.get() == "match":
            track1_end = get_track_end_time(1)
            frames_to_fill = track1_end - current_timeline_pos
            if frames_to_fill <= 0:
                messagebox.showinfo("Info", "Selected track is already longer than Track 1. Nothing to add.")
                return
        else:
            # Fixed Seconds
            try:
                frames_to_fill = int(float(self.entry_total.get()) * FPS)
            except ValueError:
                messagebox.showerror("Error", "Invalid total seconds.")
                return

        # --- 3. Clip Validation (Same as before) ---
        source_clips = [(clip, folder) for var, clip, folder in self.check_vars if var.get()]
        if not source_clips:
            messagebox.showwarning("Warning", "No clips selected!")
            return

        valid_clips = []
        for clip, folder in source_clips:
            c_type = clip.GetClipProperty("Type")
            is_still = "Still" in c_type or "Image" in c_type
            if is_still:
                 valid_clips.append((clip, 999999, True, folder))
            else:
                dur = clip.GetClipProperty("Duration")
                if dur:
                    f = parse_timecode_to_frames(dur)
                    if f > 0: valid_clips.append((clip, f, False, folder))

        if not valid_clips:
            messagebox.showerror("Error", "No valid clips found.")
            return

        # --- Slice Settings ---
        try:
            min_f = int(float(self.entry_min.get()) * FPS)
            max_f = int(float(self.entry_max.get()) * FPS)
        except ValueError:
            messagebox.showerror("Error", "Invalid min/max seconds.")
            return

        # ==========================================================
        # GENERATION LOOP
        # ==========================================================
        filled_so_far = 0
        clips_added = 0
        consecutive_failures = 0

        try:
            while filled_so_far < frames_to_fill:
                clip, clip_total_frames, is_still, folder = random.choice(valid_clips)

                slice_frames = random.randint(min_f, max_f)
                if not is_still:
                    slice_frames = min(slice_frames, clip_total_frames)
                
                remaining = frames_to_fill - filled_so_far
                if slice_frames > remaining:
                    slice_frames = remaining
                
                start_offset = 0
                if not is_still:
                    max_offset = clip_total_frames - slice_frames
                    if max_offset > 0:
                        start_offset = random.randint(0, max_offset)

                # Record Frame = Start pos + what we've added so far
                record_pos = current_timeline_pos + filled_so_far
                
                clip_info = {
                    "mediaPoolItem": clip,
                    "startFrame": start_offset,
                    "endFrame": start_offset + slice_frames,
                    "mediaType": 1, 
                    "trackIndex": dest_track_idx,
                    "recordFrame": record_pos
                }
                
                if is_still:
                    clip_info = {
                        "mediaPoolItem": clip,
                        "mediaType": 1,
                        "trackIndex": dest_track_idx,
                        "recordFrame": record_pos
                    }

                # Change directory to support bins
                media_pool.SetCurrentFolder(folder)
                
                # Append slice to timeline
                items = media_pool.AppendToTimeline([clip_info])

                if items and items[0]:
                    if is_still: items[0].Resize(slice_frames)
                    
                    filled_so_far += slice_frames
                    clips_added += 1
                    consecutive_failures = 0
                    
                    progress = (filled_so_far / frames_to_fill) * 100
                    self.log(f"Added {clip.GetName()} on V{dest_track_idx} ({progress:.1f}%)")
                else:
                    consecutive_failures += 1
                    self.log(f"FAILED to append {clip.GetName()}")
                    if consecutive_failures >= 5:
                        break

            messagebox.showinfo("Done", f"Added {clips_added} clips to V{dest_track_idx}")
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            # Restore media pool folder to root
            if media_pool:
                root = media_pool.GetRootFolder()
                media_pool.SetCurrentFolder(root)
            
            self.log("Done.")
            
if __name__ == "__main__":
    if resolve:
        root = tk.Tk()
        root.attributes("-topmost", True) 
        app_gui = BRollGenerator(root)
        root.mainloop()
