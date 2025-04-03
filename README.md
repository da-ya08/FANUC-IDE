# FANUC LS Program Editor

![Screenshot](resources/screenshot.png)

Cross-platform IDE for FANUC robot programming (LS files) with syntax highlighting.

## Features

- Syntax highlighting for FANUC LS programs
- Line numbers
- Dark/Light themes
- Multi-language support (English/Russian)
- When opened, hides: heading information, numbering in the text, semicolons, points information.
- Ability to drag a .LS file onto a packed script in exe to open it
- Uploading and sending files via FTP. Same with a real robot

## Installation

1. Clone repository:
```bash
git clone https://github.com/yourname/fanuc-ide.git
cd fanuc-ide
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run:
```bash
python src/main.py
```

## Get .exe

You can also [download .exe](https://github.com/da-ya08/FANUC-IDE/releases/tag/Release).

## Usage

Open LS files, edit syntax highlighting and save.

## Use FTP

- In the FTP menu, the download function requests an FTP link (example: ftp://admin@127.0.0.1/md%3A%5Cmain.ls)
- If there is no login in the link, it is taken from [conf.py](conf.py), the _FTP_DATA_ variable
- If the file was downloaded, then when sending, it will be sent to the same place where it was downloaded
- If necessary, the file can be sent via another link "Send via link..."

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

## In the future
It is planned to add a title and point information generator.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.