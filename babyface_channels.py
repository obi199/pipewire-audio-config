# Custom Channel Mapping for RME Babyface Pro
# This file defines meaningful channel names for the Babyface Pro
# instead of generic surround sound labels

# RME Babyface Pro in Class Compliant Mode has:
# - 2 channels: Main Analog I/O (XLR)
# - 8 channels: ADAT I/O (via optical ADAT connector)
# - 2 channels: S/PDIF I/O (digital)
# Total: 12 channels

# Physical Layout:
# Outputs (to speakers/recording):
# 1-2: Main Analog Out (XLR balanced)
# 3-10: ADAT Out 1-8
# 11-12: S/PDIF Out (coaxial/optical)
#
# Inputs (from instruments/microphones):
# 1-2: Main Analog In (XLR balanced)
# 3-10: ADAT In 1-8
# 11-12: S/PDIF In

# Channel Mapping Options:

## Option 1: Simple naming (recommended for Babyface Pro)
# This makes it immediately clear what physical I/O each channel maps to

babyface_pro_simple = {
    "name": "RME Babyface Pro - Simple Names",
    "device": "Babyface Pro",
    "channels": 12,
    "layout": {
        "outputs": [
            "Main-L",        # 0: Analog Out Left (XLR)
            "Main-R",        # 1: Analog Out Right (XLR)
            "ADAT-1",        # 2: ADAT Out 1
            "ADAT-2",        # 3: ADAT Out 2
            "ADAT-3",        # 4: ADAT Out 3
            "ADAT-4",        # 5: ADAT Out 4
            "ADAT-5",        # 6: ADAT Out 5
            "ADAT-6",        # 7: ADAT Out 6
            "ADAT-7",        # 8: ADAT Out 7
            "ADAT-8",        # 9: ADAT Out 8
            "S/PDIF-L",      # 10: Digital Out Left
            "S/PDIF-R",      # 11: Digital Out Right
        ],
        "inputs": [
            "Main-L",        # 0: Analog In Left (XLR)
            "Main-R",        # 1: Analog In Right (XLR)
            "ADAT-1",        # 2: ADAT In 1
            "ADAT-2",        # 3: ADAT In 2
            "ADAT-3",        # 4: ADAT In 3
            "ADAT-4",        # 5: ADAT In 4
            "ADAT-5",        # 6: ADAT In 5
            "ADAT-6",        # 7: ADAT In 6
            "ADAT-7",        # 8: ADAT In 7
            "ADAT-8",        # 9: ADAT In 8
            "S/PDIF-L",      # 10: Digital In Left
            "S/PDIF-R",      # 11: Digital In Right
        ]
    }
}

## Option 2: Professional studio names
# Useful if routing to different destinations

babyface_pro_studio = {
    "name": "RME Babyface Pro - Studio Names",
    "device": "Babyface Pro",
    "channels": 12,
    "layout": {
        "outputs": [
            "Stereo-L",      # Main stereo output left
            "Stereo-R",      # Main stereo output right
            "Mic-1",         # ADAT mic input simulation
            "Mic-2",
            "Line-1",        # ADAT line input simulation
            "Line-2",
            "Synth-1",       # ADAT synth track
            "Synth-2",
            "Drums-1",       # ADAT drum tracks
            "Drums-2",
            "Digital-L",     # S/PDIF digital
            "Digital-R",
        ],
        "inputs": [
            "Mic-In-L",      # Main microphone input left
            "Mic-In-R",      # Main microphone input right
            "ADAT-In-1",
            "ADAT-In-2",
            "ADAT-In-3",
            "ADAT-In-4",
            "ADAT-In-5",
            "ADAT-In-6",
            "ADAT-In-7",
            "ADAT-In-8",
            "Digital-In-L",  # S/PDIF input left
            "Digital-In-R",  # S/PDIF input right
        ]
    }
}

## Option 3: Detailed technical names
# Useful for technical documentation

babyface_pro_technical = {
    "name": "RME Babyface Pro - Technical Names",
    "device": "Babyface Pro",
    "channels": 12,
    "layout": {
        "outputs": [
            "XLR-Out-L",     # Analog XLR Balanced Out L
            "XLR-Out-R",     # Analog XLR Balanced Out R
            "ADAT-Out-1",    # ADAT Optical Output 1
            "ADAT-Out-2",    # ADAT Optical Output 2
            "ADAT-Out-3",    # ADAT Optical Output 3
            "ADAT-Out-4",    # ADAT Optical Output 4
            "ADAT-Out-5",    # ADAT Optical Output 5
            "ADAT-Out-6",    # ADAT Optical Output 6
            "ADAT-Out-7",    # ADAT Optical Output 7
            "ADAT-Out-8",    # ADAT Optical Output 8
            "Coax-Out-L",    # S/PDIF Coaxial Output L
            "Coax-Out-R",    # S/PDIF Coaxial Output R
        ],
        "inputs": [
            "XLR-In-L",      # Analog XLR Balanced In L
            "XLR-In-R",      # Analog XLR Balanced In R
            "ADAT-In-1",     # ADAT Optical Input 1
            "ADAT-In-2",     # ADAT Optical Input 2
            "ADAT-In-3",     # ADAT Optical Input 3
            "ADAT-In-4",     # ADAT Optical Input 4
            "ADAT-In-5",     # ADAT Optical Input 5
            "ADAT-In-6",     # ADAT Optical Input 6
            "ADAT-In-7",     # ADAT Optical Input 7
            "ADAT-In-8",     # ADAT Optical Input 8
            "Coax-In-L",     # S/PDIF Coaxial Input L
            "Coax-In-R",     # S/PDIF Coaxial Input R
        ]
    }
}

# Usage in Python:
# from babyface_channels import babyface_pro_simple
# channels = babyface_pro_simple["layout"]["outputs"]  # Get output channel names
