# Metal Stock Management System

A web-based inventory management system designed for metal sheet tracking and scrap management.

## Features

- **Stock Management**
  - Add, edit, and delete metal sheets
  - Track thickness, type, dimensions, and quantity
  - Automatic critical stock warnings
  - Real-time stock updates

- **Scrap Management**
  - Track metal scraps with photos
  - Record dimensions and notes
  - Mark scraps as used/unused
  - Photo upload with automatic compression

- **Metal Type Management**
  - Add and remove metal types
  - Prevent deletion of types in use
  - Default metal types included

- **User Interface**
  - Responsive design for desktop and mobile
  - Dark theme
  - Sortable tables and cards
  - Interactive statistics dashboard

- **Security**
  - Password protection
  - Session management
  - "Remember me" functionality

## Technical Details

- **Backend**
  - Python Flask framework
  - SQLite database
  - SQLAlchemy ORM
  - Pillow for image processing

- **Frontend**
  - Bootstrap 5
  - SweetAlert2 for notifications
  - FontAwesome icons
  - Responsive grid system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/webalet/stok-takip.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the application:
- Create `config.py` with the following variables:
  - `SIFRE`: Login password
  - `SECRET_KEY`: Flask secret key
  - `UPLOAD_FOLDER`: Path for uploaded images
  - `MAX_CONTENT_LENGTH`: Maximum file upload size
  - `ALLOWED_EXTENSIONS`: Allowed file extensions

4. Run the application:
```bash
python app.py
```

## Usage

1. Access the application through a web browser
2. Login with the configured password
3. Use the navigation menu to switch between stock and scrap management
4. Add new items using the forms at the top of each page
5. Manage existing items using the table/card views
6. View statistics on the main dashboard

## Contributing

Feel free to fork the repository and submit pull requests for any improvements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

- **Onur Çam**
  - Email: onrcm@hotmail.com
  - Instagram: [@onur.cm](https://instagram.com/onur.cm) 