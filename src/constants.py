MACOS_VK_MAP = { # Virtual keycode to character
	0: 'a', 11: 'b', 8: 'c', 2: 'd', 14: 'e', 3: 'f', 5: 'g', 4: 'h', 34: 'i',
	38: 'j', 40: 'k', 37: 'l', 46: 'm', 45: 'n', 31: 'o', 35: 'p', 12: 'q',
	15: 'r', 1: 's', 17: 't', 32: 'u', 9: 'v', 13: 'w', 7: 'x', 16: 'y', 6: 'z',
	29: '0', 18: '1', 19: '2', 20: '3', 21: '4', 23: '5', 22: '6', 26: '7', 28: '8', 25: '9',
	49: 'space', 36: 'newline', 48: 'tab',
	24: '=', 27: '-', 33: '[', 30: ']', 42: '\\', 41: ';', 39: "'", 43: ',', 47: '.', 44: '/', 50: '`',
}
MACOS_INVERSE_VK_MAP = {val: key for key, val in MACOS_VK_MAP.items()}

MASTER_STYLESHEET = """
	QWidget {
		background-color: #303030;
		color: #DEDEDE;
		font-size: 13px;
	}

	QPushButton {
		background-color: #535353;
		border: 0px solid #000000;
		border-radius: 6px;
		padding: 4px 8px;
		color: #E0E0E0;
	}

	QPushButton:hover {
		background-color: #404046;
		border: 1px solid #444444;
		color: #FFFFFF;
	}

	QPushButton:pressed {
		background-color: #1A1A1A;
		border: 1px solid #222222;
	}

	QLineEdit, QTextEdit, QPlainTextEdit {
		background-color: #1A1A1A;
		border: 1px solid #2A2A2A;
		border-radius: 1px;
		padding: 5px;
		color: #FFFFFF;
	}

	QLineEdit:focus {
		border: 1px solid #555555;
	}

	/*QCheckBox::indicator {
		width: 16px;
		height: 16px;
		background-color: #1A1A1A;
		border: 2px solid #444444;
		border-radius: 4px;
	}

	QCheckBox::indicator:checked {
		background-color: #00B467;
	}*/

	QCheckBox::indicator {
    	width: 16px;
   		height: 16px;
	}


	QScrollBar:vertical {
		border: none;
		background: #121212;
		width: 8px;
	}

	QScrollBar::handle:vertical {
		background: #333333;
		min-height: 20px;
		border-radius: 4px;
	}

	QScrollBar::handle:vertical:hover {
		background: #444444;
	}
	QScrollBar:horizontal {
		border: none;
		background: #121212;
		width: 8px;
	}

	QScrollBar::handle:horizontal {
		background: #333333;
		min-height: 20px;
		border-radius: 4px;
	}

	QScrollBar::handle:horizontal:hover {
		background: #444444;
	}

	QLabel#heading {
		color: #FFFFFF;
		font-weight: bold;
		font-size: 16px;
	}
	QLabel#script-status-long {
		color: #BDBDBD;
		font-size: 8px;
	}
	QPushButton#info-popup {
		border-radius: 8px;
		background-color: #535353;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#info-popup {
	}
	QPushButton:hover#info-popup {
	}
	QPushButton#status-red {
		border-radius: 8px;
		background-color: #FF0000;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-red {
	}
	QPushButton:hover#status-red {
	}
	QPushButton#status-green {
		border-radius: 8px;
		background-color: #32FF64;
		color: #000000;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-green {
	}
	QPushButton:hover#status-green {
	}
	QPushButton#status-yellow {
		border-radius: 8px;
		background-color: #FFFA05;
		color: #000000;
		border: 1px solid #000000;
		width: 16px;
   		height: 16px;
		margin: 0;
        padding: 0;
	}
	QPushButton:pressed#status-yellow {
	}
	QPushButton:hover#status-yellow {
	}
"""
