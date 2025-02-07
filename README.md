# Manga Downloader

A Python script that allows you to download manga chapters from the MangaDex.

## Installation

1. Clone the repository:
```
git clone https://github.com/Randis12345/mangadex-downloader.git
```
2. Install the required dependencies:
```
pip install -r requirements.txt
```

## Usage

To use the script, run the following command:

```
python manga-downloader.py --id <manga_id> --chapter <chapter_range> --path <download_path> --language <language_code> --prefix <file_prefix> --overwrite
```

Here's a breakdown of the available arguments:

- `--id`: The MangaDex ID of the manga you want to download.
- `--chapter`: The chapter(s) you want to download. You can specify a range (e.g., `1,10`), a single chapter number (e.g., `3`), or `all` to download all chapters.
- `--path`: The directory where the downloaded chapters will be saved (default is the current working directory).
- `--language`: The language of the manga chapters you want to download (default is "en" for English).
- `--prefix`: The prefix used for the downloaded chapter files (default is "chapter").
- `--overwrite`: If set, the script will overwrite existing chapter files.

you can also run
```
python manga-downloader.py --help
```


## Contributing

If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
