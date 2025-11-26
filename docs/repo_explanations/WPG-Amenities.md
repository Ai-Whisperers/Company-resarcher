# WPG-Amenities

**Description:** 
**URL:** https://github.com/Ai-Whisperers/WPG-Amenities
**Visibility:** PUBLIC

---

# WPG Amenities Website

Professional website for WPG Amenities, a leading provider of high-quality hotel amenity solutions in Paraguay.

## 🚀 Quick Start

### Run the website locally:

```bash
# Using Python (recommended)
cd public
python -m http.server 8000

# Or using npm scripts
npm run start
```

Then open http://localhost:8000 in your browser.

## 📁 Project Structure

```
wpg-amenities/
├── public/                 # Website files
│   ├── index.html         # Homepage
│   ├── products.html      # Products main page
│   ├── products/          # Product category pages
│   │   ├── bottles-caps.html
│   │   ├── soaps-liquids.html
│   │   └── amenity-kits.html
│   ├── css/               # Stylesheets
│   │   ├── modern-style.css    # Main styles
│   │   ├── _variables.css      # CSS variables
│   │   ├── page-specific.css   # Page-specific styles
│   │   └── footer-enhanced.css # Footer styles
│   ├── js/                # JavaScript files
│   │   ├── main.js            # Main application
│   │   ├── config.js          # Configuration
│   │   ├── placeholder.js     # Image placeholder system
│   │   ├── template-engine.js # Template utilities
│   │   └── vendor/            # Third-party libraries
│   ├── data/              # Content data
│   │   └── content.yml        # All site content
│   ├── partials/          # HTML partials
│   │   ├── header.html
│   │   └── footer.html
│   └── images/            # Image assets (empty - uses placeholders)
├── package.json           # Project configuration
├── README.md             # This file
└── IMAGE_REQUIREMENTS.md  # Image specifications

```

## 🎨 Features

- **Modern Responsive Design**: Mobile-first approach with responsive layouts
- **Dynamic Content Loading**: Content managed via YAML configuration
- **Placeholder System**: Automatic placeholder generation for missing images
- **Error Handling**: Graceful fallbacks for missing resources
- **SEO Optimized**: Meta tags, semantic HTML, and structured data
- **Accessibility**: WCAG compliant with ARIA labels and keyboard navigation

## 🛠️ Technology Stack

- **Frontend**: Vanilla JavaScript (ES6+)
- **Styling**: Modern CSS with custom properties
- **Data**: YAML configuration files
- **Build**: No build process required (runs directly)

## 📝 Configuration

### Production/Development Mode

Edit `public/js/config.js`:

```javascript
const config = {
    production: true,  // Set to false for debug logs
    // ...
};
```

### Content Management

All website content is managed in `public/data/content.yml`. Edit this file to update:
- Product listings
- Company information
- Page content
- Navigation menus
- Footer information

## 🖼️ Images

The website uses a placeholder system for missing images. To add real images:

1. Check `IMAGE_REQUIREMENTS.md` for specifications
2. Add images to the appropriate folders in `public/images/`
3. Images will automatically replace placeholders

## 🚦 Development

### Start Development Server

```bash
npm run dev
# or
python -m http.server 8000 -d public
```

### Enable Debug Mode

Set `production: false` in `public/js/config.js` to enable console logging.

## 📋 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## 🔧 Troubleshooting

### Images Not Loading
- The placeholder system will automatically generate placeholder images
- Check browser console for any errors
- Ensure image paths match those in `content.yml`

### Content Not Displaying
- Verify `content.yml` is properly formatted
- Check browser console for YAML parsing errors
- Ensure js-yaml library is loaded

### Page Not Found
- All pages should be accessed from a web server
- Direct file:// access may not work due to CORS restrictions

## 📄 License

© 2024 WPG Amenities. All rights reserved.

## 📧 Contact

For questions or support regarding this website:
- Email: info@wpgamenities.com
- Phone: +595 21 213-621

---

Built with ❤️ for WPG Amenities