// Fire Sac ekleme fonksiyonu
async function fireSacEkle(event) {
    event.preventDefault();
    
    try {
        const form = document.getElementById('fireSacEkleForm');
        const formData = new FormData(form);
        
        const response = await fetch('/fire-sac/ekle', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
        }

        await Swal.fire({
            title: 'Başarılı!',
            text: 'Fire sac başarıyla eklendi.',
            icon: 'success',
            confirmButtonText: 'Tamam'
        });

        window.location.reload();
    } catch (error) {
        await Swal.fire({
            title: 'Hata!',
            text: error.message || 'Fire sac eklenirken bir hata oluştu.',
            icon: 'error',
            confirmButtonText: 'Tamam'
        });
    }
}

// Fire Sac silme fonksiyonu
async function fireSacSil(id) {
    try {
        const result = await Swal.fire({
            title: 'Emin misiniz?',
            text: 'Bu fire sacı silmek istediğinizden emin misiniz?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Evet, Sil',
            cancelButtonText: 'İptal',
            confirmButtonColor: '#e63946',
            cancelButtonColor: '#1a1a2e'
        });

        if (result.isConfirmed) {
            const element = document.querySelector(`[data-fire-id="${id}"]`);
            if (!element) {
                throw new Error('Element bulunamadı');
            }

            const group = element.closest('.kalinlik-group');
            const groupHeader = group ? group.querySelector('.kalinlik-title') : null;

            const response = await fetch(`/fire-sac/sil/${id}`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Silme işlemi başarısız oldu');
            }

            const data = await response.json();
            if (!data.success) {
                throw new Error(data.message || 'Silme işlemi başarısız oldu');
            }

            // Önce fade-out animasyonu uygula
            element.style.transition = 'opacity 0.3s ease';
            element.style.opacity = '0';

            await new Promise(resolve => setTimeout(resolve, 300));

            // Elementi kaldır
            element.remove();

            // Gruptaki eleman sayısını kontrol et
            if (group) {
                const remainingItems = group.querySelectorAll('[data-fire-id]:not([style*="opacity: 0"])');
                const count = remainingItems.length;
                const badge = groupHeader ? groupHeader.querySelector('.badge') : null;
                
                if (badge) {
                    badge.textContent = `${count} adet`;
                }

                // Grup boşsa kaldır
                if (count === 0) {
                    if (groupHeader) {
                        groupHeader.style.transition = 'opacity 0.3s ease';
                        groupHeader.style.opacity = '0';
                    }
                    
                    group.style.transition = 'all 0.3s ease';
                    group.style.opacity = '0';
                    group.style.maxHeight = '0';
                    group.style.overflow = 'hidden';
                    
                    await new Promise(resolve => setTimeout(resolve, 300));
                    group.remove();
                }
            }

            await Swal.fire({
                title: 'Başarılı!',
                text: 'Fire sac başarıyla silindi.',
                icon: 'success',
                timer: 1500,
                showConfirmButton: false
            });
        }
    } catch (error) {
        console.error('Silme hatası:', error);
        await Swal.fire({
            title: 'Hata!',
            text: error.message || 'Silme işlemi sırasında bir hata oluştu.',
            icon: 'error'
        });
    }
}

// Grup sayısını güncelleme ve grup silme fonksiyonu
async function updateGroupCount(element) {
    const group = element.closest('.kalinlik-group');
    if (group) {
        const badge = group.querySelector('.badge');
        if (badge) {
            const count = parseInt(badge.textContent);
            if (!isNaN(count)) {
                const newCount = count - 1;
                badge.textContent = `${newCount} adet`;
                
                // Gruptaki son eleman silindiyse
                if (newCount === 0) {
                    // Masaüstü görünümü için tablo içeriğini kontrol et
                    const tableContent = group.querySelector('.table tbody');
                    if (tableContent && tableContent.children.length === 0) {
                        await removeGroup(group);
                    }
                    
                    // Mobil görünüm için kart içeriğini kontrol et
                    const cardContent = group.querySelector('.fire-sac-container');
                    if (cardContent && cardContent.children.length === 0) {
                        await removeGroup(group);
                    }
                }
            }
        }
    }
}

// Grup silme animasyonu ve kaldırma
async function removeGroup(group) {
    // Önce yüksekliği sabitle
    const groupHeight = group.offsetHeight;
    group.style.height = groupHeight + 'px';
    
    // Reflow için gerekli
    group.offsetHeight;
    
    // Animasyon sınıfını ekle
    group.classList.add('removing');
    
    // Yüksekliği sıfıra indir
    group.style.height = '0';
    group.style.marginBottom = '0';
    group.style.paddingBottom = '0';
    
    // Animasyon bitince elementi kaldır
    await new Promise(resolve => setTimeout(resolve, 500));
    group.remove();
}

// Resim önizleme fonksiyonu
function resimOnizle(input) {
    const preview = document.getElementById('resimOnizleme');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        };
        
        reader.readAsDataURL(input.files[0]);
    } else {
        preview.style.display = 'none';
    }
}

// Resim tıklama olayı
$(document).on('click', '.fire-image', function() {
    var imgSrc = $(this).attr('src');
    $('#modalImage').attr('src', imgSrc);
    $('#imageModal').modal('show');
});

let scale = 1;
let isZoomed = false;

$('#modalImage').on('click', function(e) {
    if (!isZoomed) {
        scale = 2;
        $(this).css('transform', `scale(${scale})`);
    } else {
        scale = 1;
        $(this).css('transform', 'scale(1)');
    }
    isZoomed = !isZoomed;
});

// Mobil silme işlemi
$(document).on('click', '.delete-button', function(e) {
    e.preventDefault();
    const row = $(this).closest('.fire-card');
    const deleteUrl = $(this).attr('href');
    
    if (confirm('Bu kaydı silmek istediğinizden emin misiniz?')) {
        $.ajax({
            url: deleteUrl,
            type: 'GET',
            success: function(response) {
                row.fadeOut(400, function() {
                    row.remove();
                    // Grup içindeki son eleman silindiyse grubu da kaldır
                    $('.group-container').each(function() {
                        if ($(this).find('.fire-card').length === 0) {
                            $(this).fadeOut(400, function() {
                                $(this).remove();
                            });
                        }
                    });
                });
            },
            error: function(xhr, status, error) {
                alert('Silme işlemi sırasında bir hata oluştu.');
            }
        });
    }
});

// Grup açma/kapama fonksiyonu
function toggleGroup(element) {
    const groupId = element.getAttribute('data-group');
    const content = document.getElementById(groupId);
    if (content) {
        content.classList.toggle('show');
        const icon = element.querySelector('.toggle-icon');
        if (icon) {
            icon.classList.toggle('rotated');
        }
        
        // Animasyon için scroll
        if (content.classList.contains('show')) {
            content.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}

// Durum değiştirme fonksiyonu
async function durumDegistir(id, element) {
    try {
        const response = await fetch(`/fire-sac/durum/${id}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Durum değiştirme başarısız oldu');
        }

        const data = await response.json();
        
        if (data.success) {
            // Buton rengini ve sınıflarını güncelle
            element.classList.remove('btn-forest', 'btn-warning', 'active', 'inactive');
            element.classList.add(data.kullaniliyor ? 'btn-warning' : 'btn-forest');
            element.classList.add(data.kullaniliyor ? 'active' : 'inactive');
            
            // İkon ve metni güncelle
            const icon = element.querySelector('i') || document.createElement('i');
            icon.className = `fas ${data.kullaniliyor ? 'fa-times' : 'fa-check'} me-1`;
            
            if (!element.querySelector('i')) {
                element.prepend(icon);
            }
            
            // Buton metnini güncelle
            element.innerHTML = '';
            element.appendChild(icon);
            element.appendChild(document.createTextNode(data.kullaniliyor ? 'Kullanılıyor' : 'Kullanılmıyor'));
            
            // Title güncelle
            element.title = data.kullaniliyor ? 'Kullanılıyor' : 'Kullanılmıyor';
        } else {
            throw new Error('Durum güncellenirken bir hata oluştu');
        }
    } catch (error) {
        await Swal.fire({
            title: 'Hata!',
            text: error.message,
            icon: 'error',
            confirmButtonText: 'Tamam'
        });
    }
}

// Mobil sıralama fonksiyonları
let siralama = {
    alan: null,
    yon: 'asc'
};

function mobilSirala(alan) {
    const tbody = document.querySelector('tbody');
    if (!tbody) return;
    
    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (rows.length === 0) return;
    
    // Sıralama yönünü güncelle
    if (siralama.alan === alan) {
        siralama.yon = siralama.yon === 'asc' ? 'desc' : 'asc';
    } else {
        siralama.alan = alan;
        siralama.yon = 'asc';
    }
    
    // Aktif sıralama butonunu güncelle
    document.querySelectorAll('.mobile-sort-buttons .btn').forEach(btn => {
        if (!btn) return;
        btn.classList.remove('btn-primary', 'btn-outline-primary');
        if (btn.getAttribute('data-sort') === alan) {
            btn.classList.add('btn-primary');
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = `fas fa-sort-${siralama.yon === 'asc' ? 'up' : 'down'}`;
            }
        } else {
            btn.classList.add('btn-outline-primary');
            const icon = btn.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-sort';
            }
        }
    });
    
    // Sıralama fonksiyonu
    rows.sort((a, b) => {
        let aVal, bVal;
        const aElement = a.querySelector(`[data-${alan}]`);
        const bElement = b.querySelector(`[data-${alan}]`);
        
        if (!aElement || !bElement) return 0;
        
        switch(alan) {
            case 'kalinlik':
            case 'en':
            case 'boy':
                aVal = parseFloat(aElement.getAttribute(`data-${alan}`)) || 0;
                bVal = parseFloat(bElement.getAttribute(`data-${alan}`)) || 0;
                break;
            case 'tarih':
                aVal = new Date(aElement.getAttribute('data-tarih')) || new Date(0);
                bVal = new Date(bElement.getAttribute('data-tarih')) || new Date(0);
                break;
            default:
                aVal = aElement.getAttribute(`data-${alan}`)?.toLowerCase() || '';
                bVal = bElement.getAttribute(`data-${alan}`)?.toLowerCase() || '';
        }
        
        if (siralama.yon === 'asc') {
            return aVal > bVal ? 1 : -1;
        } else {
            return aVal < bVal ? 1 : -1;
        }
    });
    
    // DOM'u güncelle
    rows.forEach(row => tbody.appendChild(row));
}

// Sayfa yüklendiğinde varsayılan sıralama
document.addEventListener('DOMContentLoaded', () => {
    // Varsayılan sıralama: Tarih (en yeni)
    mobilSirala('tarih');
});

// Grup başlıklarına tıklama olayı
document.addEventListener('DOMContentLoaded', function() {
    // Sayfa yüklendiğinde tüm içerikleri gizle (hem tablo hem mobil kartlar)
    document.querySelectorAll('.kalinlik-group table, .kalinlik-group .fire-sac-container').forEach(content => {
        content.style.display = 'none';
    });

    // Tüm grup başlıklarını seç
    const titles = document.querySelectorAll('.kalinlik-title');
    
    titles.forEach(title => {
        // Tıklama olayını ekle
        title.addEventListener('click', function() {
            const group = this.closest('.kalinlik-group');
            // Hem tablo hem mobil kart içeriğini kontrol et
            const content = group.querySelector('table') || group.querySelector('.fire-sac-container');
            
            if (content) {
                const isVisible = window.getComputedStyle(content).display !== 'none';
                // İçerik tipine göre display değerini ayarla
                if (isVisible) {
                    content.style.display = 'none';
                } else {
                    content.style.display = content.tagName.toLowerCase() === 'table' ? 'table' : 'block';
                }
            }
        });
    });
});

// Sayfa yüklendiğinde event listener'ları ekle
document.addEventListener('DOMContentLoaded', function() {
    // Masaüstü ve mobil görünüm için sil butonlarına event listener ekle
    const addDeleteHandlers = () => {
        document.querySelectorAll('.btn-danger[onclick*="fireSacSil"]').forEach(button => {
            button.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                const id = this.closest('[data-fire-id]').getAttribute('data-fire-id');
                if (id) fireSacSil(id);
                return false;
            };
        });
    };

    // İlk yüklemede event listener'ları ekle
    addDeleteHandlers();

    // DOM değişikliklerini izle
    const observer = new MutationObserver(addDeleteHandlers);
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}); 