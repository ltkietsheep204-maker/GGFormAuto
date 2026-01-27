# 🚀 Google Form Auto Filler - Setup Guide

**Version**: 3.1 (Headless + Parallel Processing + Random Mode)

## System Requirements

### Windows
- Windows 7 or later (Windows 10/11 recommended)
- 4GB RAM minimum
- 500MB free disk space
- Google Chrome browser installed

### macOS
- macOS 10.14 or later
- 4GB RAM minimum
- 500MB free disk space
- Google Chrome browser installed

### Linux
- Ubuntu 18.04 or later
- 4GB RAM minimum
- 500MB free disk space
- Google Chrome browser installed

## Installation

### Windows

1. **Download** `GoogleFormAutoFiller-Windows.zip`
2. **Extract** to a folder (right-click → "Extract All")
3. **Double-click** `Google Form Auto Filler.exe`
4. **Allow** Windows Defender/Firewall if prompted

> 💡 If Windows shows "SmartScreen warning", click "More info" → "Run anyway"

### macOS

1. **Download** `GoogleFormAutoFiller-macOS.zip`
2. **Extract** by double-clicking the file
3. **Quarantine workaround** (if needed):
   ```bash
   xattr -d com.apple.quarantine "/Applications/Google Form Auto Filler.app"
   ```
4. **Double-click** `Google Form Auto Filler.app`
5. **Allow** in Security & Privacy if prompted

> 💡 First time may be slow as macOS checks the app

### Linux

1. **Download** `GoogleFormAutoFiller-Linux.tar.gz`
2. **Extract**:
   ```bash
   tar -xzf GoogleFormAutoFiller-Linux.tar.gz
   ```
3. **Make executable**:
   ```bash
   chmod +x "Google Form Auto Filler"
   ```
4. **Run**:
   ```bash
   ./"Google Form Auto Filler"
   ```

## First-Time Setup

### 1️⃣ Enable Chrome

The app uses Google Chrome/Chromium:
- ✅ Chrome must be installed
- ✅ App runs Chrome in **headless mode** (invisible)
- ✅ No Chrome windows will appear (cleaner experience!)

### 2️⃣ Prepare Your Form

Get your Google Form link:
1. Open Google Form (on web)
2. Click "Share" → Copy link
3. Example: `https://forms.gle/abc123xyz`

### 3️⃣ Run the App

1. **Launch** Google Form Auto Filler
2. **Paste** form URL in the URL input
3. **Click** "📥 Tải Thông Tin Form" (Load Form)
4. **Wait** for form to load (5-10 seconds)
5. **Choose answers** from the displayed options

## Features

### ✨ Main Features

| Feature | Details |
|---------|---------|
| **🔍 Auto Extract** | Automatically reads all questions & options |
| **☑️ Visual Selection** | Click answers like in the real form |
| **🎲 Random Mode** | Choose multiple answers with percentage distribution |
| **⚡ Parallel Processing** | Run 1-5 Chrome tabs simultaneously |
| **🔒 Headless Mode** | Chrome runs hidden (no visual clutter) |
| **📊 Smart Validation** | Ensures percentages = 100% |
| **📋 Progress Tracking** | Real-time submission progress |

### 🎲 Random Mode Example

**Normal Mode** (off):
- Choose 1 answer → All responses use same answer

**Random Mode** (on):
- Choose multiple answers + set percentages
- Example: A=25%, B=35%, C=40%
- Each submission picks randomly based on percentages

### ⚡ Parallel Processing

**Sequential** (1 tab):
- 100 responses = ~5 minutes
- Easy to monitor

**Parallel** (5 tabs):
- 100 responses = ~1 minute
- 5x faster!
- Still respects percentage distribution

## Usage Guide

### Step 1: Load Form

```
1. Paste Google Form URL
   https://forms.gle/...
2. Click 📥 "Tải Thông Tin Form"
3. Wait for questions to load
```

### Step 2: Choose Answers (Tab: Chọn Đáp Án)

**Normal Mode:**
```
☑ Bật tính năng: OFF
Q1. What color?
  ⦿ Red
  ○ Blue
  ○ Green
(Pick one)
```

**Random Mode:**
```
☑ Bật tính năng: ON
Q1. What color?
  ☑ Red    Tỉ lệ: [25]%
  ☑ Blue   Tỉ lệ: [35]%
  ☑ Green  Tỉ lệ: [40]%
(Total = 100%)
```

### Step 3: Configure Submission (Tab: Gửi Responses)

```
Số lượng responses: [100]
⚡ Số tabs Chrome: [5]  (1=slow, 5=fast)
📤 Bắt Đầu Gửi → Click to submit
```

### Step 4: Monitor Progress

- Real-time log shows submissions
- Progress bar updates
- When done: "✅ Hoàn tát!"

## Tips & Tricks

### ✅ Performance

- **Fast Mode**: Use 5 parallel tabs
- **Stable Mode**: Use 2-3 parallel tabs
- **Conservative**: Use 1 parallel tab

### ✅ Random Mode Best Practices

- Always ensure percentages = 100%
- Common distributions:
  - Equal: 25%, 25%, 25%, 25%
  - Weighted: 50%, 30%, 20%
  - Extreme: 80%, 20%

### ✅ Large Batches

- For 1000+ responses:
  - Use maximum parallel tabs (5)
  - Consider doing multiple batches
  - Each batch doesn't affect others

### ⚠️ Common Issues

**"Form not loading"**
- Check URL is correct
- Try copying URL again
- Ensure form is not restricted

**"Chrome not found"**
- Install Google Chrome: https://google.com/chrome
- Or use Chromium: https://chromium.woolyss.com

**"Random percentage error"**
- Check: Do percentages = 100%?
- Example: 25% + 25% + 50% = 100% ✅
- Not: 25% + 25% + 25% = 75% ❌

**"Slow submission"**
- Reduce parallel tabs to 3
- Or use sequential mode (1 tab)

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+Q` | Quit application |
| `Ctrl+L` | Focus URL input |

## Data Privacy

- ✅ All data processing is local
- ✅ No data sent to external servers
- ✅ Chrome runs on your computer
- ✅ Form submissions go directly to Google Forms
- ✅ Your answers are never stored

## Uninstallation

### Windows
- Right-click app → Delete
- Or move to Trash

### macOS
- Drag app to Trash
- Or delete from Applications

### Linux
- `rm -rf "Google Form Auto Filler"`

## Getting Help

### Troubleshooting

1. **Restart the application**
2. **Check Chrome is installed**
3. **Try a different form URL**
4. **Look at the error message in log**

### Common Error Messages

| Error | Solution |
|-------|----------|
| "Form not loaded" | Verify URL and try again |
| "Could not find submit button" | Form may have changed structure |
| "Chrome not found" | Install Google Chrome |
| "Percentage validation" | Ensure total % = 100% |

## Updates

Check for new versions:
- Download latest from Google Drive
- Or request update from developer

## Feedback

Found a bug or have suggestions? 
- Note down what happened
- Check the error log
- Share with developer

---

## FAQ

**Q: Does this require internet?**
A: Yes, to access Google Forms

**Q: Is this safe?**
A: Yes, it's open-source and local processing

**Q: Can I use this on multiple forms?**
A: Yes, one at a time

**Q: How many responses can I send?**
A: Depends on your quota (usually 1-10k/day)

**Q: Will Google detect this?**
A: It uses real Chrome, so minimal detection risk

**Q: Can I pause submission?**
A: Yes, close the app (current batch only)

---

**Version**: 3.1  
**Last Updated**: January 25, 2026  
**Support**: Check README_BUILD.md for technical details
