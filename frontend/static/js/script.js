const state = {
    currentType: 'url',
    data: {}
};

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

const debouncedGenerate = debounce(() => {
    generateQR(true); // pass true for silent/real-time mode
}, 500);

const formConfigs = {
    url: [
        { name: 'url', label: 'Website URL', type: 'url', placeholder: 'https://example.com', required: true }
    ],
    text: [
        { name: 'text', label: 'Your Text', type: 'textarea', placeholder: 'Enter your text here...', required: true }
    ],
    wifi: [
        { name: 'ssid', label: 'Network Name (SSID)', type: 'text', placeholder: 'MyWiFi', required: true },
        { name: 'password', label: 'Password', type: 'text', placeholder: 'Password', required: false },
        { name: 'encryption', label: 'Encryption', type: 'select', options: ['WPA/WPA2', 'WEP', 'nopass'], required: true }
    ],
    mail: [
        { name: 'email', label: 'Email', type: 'email', placeholder: 'name@example.com', required: true },
        { name: 'subject', label: 'Subject', type: 'text', placeholder: 'Hello', required: false },
        { name: 'body', label: 'Message', type: 'textarea', placeholder: 'Your message...', required: false }
    ],
    phone: [
        { name: 'phone', label: 'Phone Number', type: 'tel', placeholder: '+1 234 567 8900', required: true }
    ],
    sms: [
        { name: 'phone', label: 'Phone Number', type: 'tel', placeholder: '+1 234 567 8900', required: true },
        { name: 'message', label: 'Message', type: 'textarea', placeholder: 'Hello...', required: false }
    ],
    whatsapp: [
        { name: 'phone', label: 'WhatsApp Number', type: 'tel', placeholder: '+1 234 567 8900', required: true },
        { name: 'message', label: 'Message', type: 'textarea', placeholder: 'Hello...', required: false }
    ],
    youtube: [
        { name: 'url', label: 'YouTube Video URL', type: 'url', placeholder: 'https://youtube.com/watch?v=...', required: true }
    ],
    instagram: [
        { name: 'username', label: 'Instagram Username', type: 'text', placeholder: 'username', required: true }
    ],
    facebook: [
        { name: 'url', label: 'Facebook Page/Profile URL', type: 'url', placeholder: 'https://facebook.com/...', required: true }
    ],
    tiktok: [
        { name: 'username', label: 'TikTok Username', type: 'text', placeholder: '@username', required: true }
    ],
    telegram: [
        { name: 'username', label: 'Telegram Username', type: 'text', placeholder: 'username', required: true }
    ],
    maps: [
        { name: 'latitude', label: 'Latitude', type: 'text', placeholder: '40.7128', required: true },
        { name: 'longitude', label: 'Longitude', type: 'text', placeholder: '-74.0060', required: true }
    ],
    app: [
        { name: 'play_store', label: 'Google Play URL', type: 'url', placeholder: 'https://play.google.com/...', required: false },
        { name: 'app_store', label: 'App Store URL', type: 'url', placeholder: 'https://apps.apple.com/...', required: false }
    ],
    image: [
        { name: 'file', label: 'Upload Image', type: 'file', accept: 'image/*', required: true }
    ],
    pdf: [
        { name: 'file', label: 'Upload PDF', type: 'file', accept: 'application/pdf', required: true }
    ],
    audio: [
        { name: 'file', label: 'Upload Audio', type: 'file', accept: 'audio/*', required: true }
    ],
    video: [
        { name: 'file', label: 'Upload Video', type: 'file', accept: 'video/*', required: true }
    ],
    pptx: [
        { name: 'file', label: 'Upload PPTX', type: 'file', accept: '.pptx,.ppt', required: true }
    ],
    vcard: [
        { name: 'firstname', label: 'First Name', type: 'text', placeholder: 'John', required: true },
        { name: 'lastname', label: 'Last Name', type: 'text', placeholder: 'Doe', required: true },
        { name: 'phone', label: 'Phone', type: 'tel', placeholder: '+1 234...', required: true },
        { name: 'email', label: 'Email', type: 'email', placeholder: 'john@example.com', required: false },
        { name: 'website', label: 'Website', type: 'url', placeholder: 'https://...', required: false },
        { name: 'company', label: 'Company', type: 'text', placeholder: 'Company Inc.', required: false },
        { name: 'job', label: 'Job Title', type: 'text', placeholder: 'Manager', required: false },
        { name: 'address', label: 'Address', type: 'text', placeholder: 'Street, City...', required: false }
    ],
    event: [
        { name: 'title', label: 'Event Title', type: 'text', placeholder: 'My Party', required: true },
        { name: 'location', label: 'Location', type: 'text', placeholder: 'New York, NY', required: true },
        { name: 'start_date', label: 'Start Date/Time', type: 'datetime-local', required: true },
        { name: 'end_date', label: 'End Date/Time', type: 'datetime-local', required: true }
    ],
    crypto: [
        { name: 'currency', label: 'Currency', type: 'select', options: ['bitcoin', 'ethereum', 'litecoin'], required: true },
        { name: 'address', label: 'Wallet Address', type: 'text', placeholder: '0x...', required: true },
        { name: 'amount', label: 'Amount', type: 'number', step: '0.000001', placeholder: '0.1', required: false }
    ],
    list_links: [
        { name: 'url', label: 'Link Page URL (Demo)', type: 'url', placeholder: 'https://linktr.ee/...', required: true }
    ],
    coupon: [
        { name: 'url', label: 'Coupon URL', type: 'url', placeholder: 'https://...', required: true }
    ],
    playlist: [
        { name: 'url', label: 'Playlist URL', type: 'url', placeholder: 'https://spotify.com/...', required: true }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('inputDetails')) {
        // Check for 'type' query parameter
        const urlParams = new URLSearchParams(window.location.search);
        const typeParam = urlParams.get('type');

        if (typeParam && formConfigs[typeParam]) {
            renderForm(typeParam);
            // Update active state in grid
            document.querySelectorAll('.type-btn').forEach(btn => btn.classList.remove('active'));
            // Find button with onclick="selectType('typeParam')" - simplified check
            const activeBtn = Array.from(document.querySelectorAll('.type-btn')).find(btn =>
                btn.getAttribute('onclick').includes(`'${typeParam}'`)
            );
            if (activeBtn) activeBtn.classList.add('active');

            // Scroll to generator
            document.querySelector('.generator-layout').scrollIntoView({ behavior: 'smooth' });
        } else {
            renderForm('url');
        }
    }
});

function selectType(type) {
    state.currentType = type;

    // Update UI
    document.querySelectorAll('.type-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.querySelector('span').textContent.toLowerCase().includes(type) ||
            btn.getAttribute('onclick')?.includes(type)) {
            btn.classList.add('active');
        }
    });

    renderForm(type);
}

function renderForm(type) {
    const container = document.getElementById('inputDetails');
    container.innerHTML = '';

    const config = formConfigs[type] || formConfigs['url'];

    config.forEach(field => {
        const wrapper = document.createElement('div');
        wrapper.className = 'form-group';

        const label = document.createElement('label');
        label.textContent = field.label;
        wrapper.appendChild(label);

        let input;

        if (field.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = 4;
        } else if (field.type === 'select') {
            input = document.createElement('select');
            field.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                input.appendChild(option);
            });
        } else {
            input = document.createElement('input');
            input.type = field.type;
            if (field.accept) input.accept = field.accept;
        }

        input.className = 'form-input';
        input.name = field.name;
        input.placeholder = field.placeholder || '';
        if (field.required) input.required = true;

        input.addEventListener('change', (e) => {
            if (field.type === 'file') {
                state.data[field.name] = e.target.files[0];
            } else {
                state.data[field.name] = e.target.value;
            }
            debouncedGenerate();
        });

        input.addEventListener('input', (e) => {
            if (field.type !== 'file') {
                state.data[field.name] = e.target.value;
                debouncedGenerate();
            }
        });

        wrapper.appendChild(input);
        container.appendChild(wrapper);
    });
}

// Logo upload handling
document.addEventListener('DOMContentLoaded', () => {
    const logoInput = document.getElementById('logoInput');
    const logoFileName = document.getElementById('logoFileName');
    const logoPreview = document.getElementById('logoPreview');
    const logoPreviewImg = document.getElementById('logoPreviewImg');
    const artisticToggle = document.getElementById('artisticModeToggle');
    const modeLabel = document.getElementById('modeLabel');
    const modeDesc = document.getElementById('modeDesc');

    if (logoInput) {
        logoInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    logoPreviewImg.src = event.target.result;
                    logoPreview.style.display = 'block';
                    logoFileName.textContent = file.name;
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Artistic mode toggle
    if (artisticToggle) {
        artisticToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                modeLabel.textContent = '🎨 Artistic Mode';
                modeDesc.textContent = 'Image blends throughout entire QR code';
            } else {
                modeLabel.textContent = 'Center Logo Mode';
                modeDesc.textContent = 'Logo appears in the center of QR code';
            }
        });
    }

    // Gate quality dropdowns by plan
    fetch('/api/plan').then(r=>r.json()).then(j => {
        const plan = (j.plan || 'free').toLowerCase();
        const pro = (plan === 'pro' || plan === 'business');
        [pngQuality, jpgQuality, svgQuality, pdfQuality].forEach(sel => {
            if (!sel) return;
            if (!pro) {
                sel.value = '480';
                Array.from(sel.options).forEach(opt => opt.disabled = opt.value !== '480');
                sel.title = 'Upgrade to Pro for 720px and 1080px downloads';
            } else {
                Array.from(sel.options).forEach(opt => opt.disabled = false);
            }
        });
    }).catch(()=>{});

    // Download buttons wiring
    const pngBtn = document.getElementById('downloadPngBtn');
    const pdfBtn = document.getElementById('downloadPdfBtn');
    const svgBtn = document.getElementById('downloadSvgBtn');
    const jpgBtn = document.getElementById('downloadJpgBtn');
    const pngQuality = document.getElementById('pngQuality');
    const jpgQuality = document.getElementById('jpgQuality');
    const svgQuality = document.getElementById('svgQuality');
    const pdfQuality = document.getElementById('pdfQuality');

    if (svgBtn) {
        svgBtn.addEventListener('click', () => {
            const preview = document.getElementById('qrPreview');
            if (!preview || !preview.firstElementChild || preview.firstElementChild.tagName.toLowerCase() !== 'svg') {
                showToast('Please render an Artistic Preview (SVG) first.', 'error');
                return;
            }
            // SVG is vector; selected "px" size is irrelevant for the file content, but we still gate selection by plan in UI.
            const svgMarkup = preview.innerHTML;
            const blob = new Blob([svgMarkup], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'qrcode.svg';
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        });
    }

    function getPreviewContent() {
        const preview = document.getElementById('qrPreview');
        if (!preview || !preview.firstElementChild) return null;
        const el = preview.firstElementChild;
        const tag = el.tagName ? el.tagName.toLowerCase() : '';
        if (tag === 'img') return { type: 'png', dataUrl: el.src };
        if (tag === 'svg') return { type: 'svg', svg: preview.innerHTML };
        return null;
    }

    function dataUrlToBlob(dataUrl) {
        const parts = dataUrl.split(',');
        const mime = parts[0].match(/:(.*?);/)[1];
        const bstr = atob(parts[1]);
        let n = bstr.length;
        const u8 = new Uint8Array(n);
        while (n--) u8[n] = bstr.charCodeAt(n);
        return new Blob([u8], { type: mime });
    }

    function download(filename, blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    }

    function rasterizeSvgToPng(svgMarkup, cb) {
        const svgBlob = new Blob([svgMarkup], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(svgBlob);
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width; canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#fff'; ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.drawImage(img, 0, 0);
            canvas.toBlob((blob) => {
                cb(blob);
                URL.revokeObjectURL(url);
            }, 'image/png');
        };
        img.src = url;
    }

    function scaleImageTo(dataUrl, targetSizePx, cb, type='image/png', quality=0.92) {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = targetSizePx; canvas.height = targetSizePx;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#fff';
            ctx.fillRect(0,0,canvas.width,canvas.height);
            // Fit image into square (assumes square preview); otherwise could scale preserving aspect
            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
            canvas.toBlob((blob) => cb(blob), type, quality);
        };
        img.src = dataUrl;
    }

    if (jpgBtn) {
        jpgBtn.addEventListener('click', () => {
            const pv = getPreviewContent();
            if (!pv) { showToast('Please generate a QR first.', 'error'); return; }
            const size = parseInt((jpgQuality && jpgQuality.value) || '480', 10);
            if (pv.type === 'svg') {
                rasterizeSvgToPng(pv.svg, (pngBlob) => {
                    const r = new FileReader();
                    r.onload = () => scaleImageTo(r.result, size, (jpgBlob) => download('qrcode.jpg', jpgBlob), 'image/jpeg', 0.92);
                    r.readAsDataURL(pngBlob);
                });
            } else if (pv.type === 'png') {
                scaleImageTo(pv.dataUrl, size, (jpgBlob) => download('qrcode.jpg', jpgBlob), 'image/jpeg', 0.92);
            }
        });
    }

    if (pngBtn) {
        pngBtn.addEventListener('click', () => {
            const pv = getPreviewContent();
            if (!pv) {
                alert('Please generate a QR first.');
                return;
            }
            const size = parseInt((pngQuality && pngQuality.value) || '480', 10);
            if (pv.type === 'svg') {
                rasterizeSvgToPng(pv.svg, (pngBlob) => {
                    const r = new FileReader();
                    r.onload = () => scaleImageTo(r.result, size, (out) => download('qrcode.png', out), 'image/png');
                    r.readAsDataURL(pngBlob);
                });
            } else if (pv.type === 'png') {
                // Resample to requested size
                const r = new FileReader();
                r.onload = () => scaleImageTo(r.result, size, (out) => download('qrcode.png', out), 'image/png');
                r.readAsDataURL(dataUrlToBlob(pv.dataUrl));
            }
        });
    }

    if (pdfBtn) {
        pdfBtn.addEventListener('click', async () => {
            const pv = getPreviewContent();
            if (!pv) {
                alert('Please generate a QR first.');
                return;
            }
            // Ensure jsPDF is available
            if (typeof window.jspdf === 'undefined' && typeof window.jsPDF === 'undefined') {
                await new Promise((resolve) => {
                    const s = document.createElement('script');
                    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                    s.onload = resolve;
                    document.body.appendChild(s);
                });
            }
            const { jsPDF } = window.jspdf || window;
            const doc = new jsPDF({ unit: 'pt', format: 'a4' });

            function placeAndSave(dataUrl) {
                const pageW = doc.internal.pageSize.getWidth();
                const pageH = doc.internal.pageSize.getHeight();
                const target = parseInt((pdfQuality && pdfQuality.value) || '480', 10);
                // Render at requested size, fit within page margins
                const size = Math.min(target, pageW - 72*2, pageH - 72*2);
                doc.addImage(dataUrl, 'PNG', (pageW-size)/2, (pageH-size)/2, size, size);
                doc.save('qrcode.pdf');
            }

            if (pv.type === 'svg') {
                rasterizeSvgToPng(pv.svg, (blob) => {
                    const r = new FileReader();
                    r.onload = () => placeAndSave(r.result);
                    r.readAsDataURL(blob);
                });
            } else if (pv.type === 'png') {
                placeAndSave(pv.dataUrl);
            }
        });
    }
});

function removeLogo() {
    const logoInput = document.getElementById('logoInput');
    const logoFileName = document.getElementById('logoFileName');
    const logoPreview = document.getElementById('logoPreview');

    logoInput.value = '';
    logoFileName.textContent = 'Click to upload image/logo';
    logoPreview.style.display = 'none';
}

async function generateQR(silent = false) {
    const currentType = state.currentType;
    const formData = new FormData();
    formData.append('csrf_token', document.querySelector('meta[name="csrf-token"]').content);
    formData.append('type', currentType);

    // Append all data fields
    const inputs = document.querySelectorAll('.input-section .form-input');
    inputs.forEach(input => {
        if (input.type === 'file') {
            if (input.files.length > 0) {
                formData.append('file', input.files[0]);
            }
        } else {
            formData.append(input.name, input.value);
        }
    });

    // Append logo if uploaded
    const logoInput = document.getElementById('logoInput');
    if (logoInput && logoInput.files.length > 0) {
        formData.append('logo', logoInput.files[0]);
    }

    // Append artistic mode flag
    const artisticToggle = document.getElementById('artisticModeToggle');
    if (artisticToggle) {
        formData.append('artistic_mode', artisticToggle.checked ? 'true' : 'false');
    }

    try {
        const generateBtn = document.querySelector('.btn-primary');
        const originalText = generateBtn.textContent;
        
        if (!silent) {
            generateBtn.textContent = 'Generating...';
            generateBtn.disabled = true;
            const preview = document.getElementById('qrPreview');
            if (preview) {
                preview.innerHTML = '<div class="skeleton-box" style="aspect-ratio: 1/1; width: 100%;"></div>';
            }
        }

        const response = await fetch('/generate', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            const preview = document.getElementById('qrPreview');
            preview.innerHTML = `<img src="${data.qr_code}" alt="Generated QR Code" style="max-width: 100%; border-radius: 8px;">`;
            
            // Record in history if it's a "real" generation (not just a real-time preview flicker)
            if (typeof historyManager !== 'undefined') {
                const label = state.data.url || state.data.text || state.data.ssid || 'QR Code';
                historyManager.add(data.qr_code, state.currentType, label);
            }
        } else {
            showToast('Error: ' + data.error, 'error');
        }

        if (!silent) {
            generateBtn.textContent = originalText;
            generateBtn.disabled = false;
        }
    } catch (error) {
        console.error('Error:', error);
        if (!silent) {
            showToast('Failed to generate QR code', 'error');
            document.querySelector('.btn-primary').textContent = 'Generate QR Code';
            document.querySelector('.btn-primary').disabled = false;
        }
    }
}
