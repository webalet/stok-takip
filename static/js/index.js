// Ana sayfa JavaScript kodları
document.addEventListener('DOMContentLoaded', function() {
    // Form gönderimi
    const stokEkleForm = document.getElementById('stokEkleForm');
    if (stokEkleForm) {
        stokEkleForm.onsubmit = async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/stok/ekle', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    Swal.fire({
                        title: 'Başarılı!',
                        text: 'Stok başarıyla eklendi.',
                        icon: 'success',
                        confirmButtonText: 'Tamam'
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    const error = await response.text();
                    throw new Error(error);
                }
            } catch (error) {
                Swal.fire({
                    title: 'Hata!',
                    text: error.message || 'Stok eklenirken bir hata oluştu.',
                    icon: 'error',
                    confirmButtonText: 'Tamam'
                });
            }
        };
    }

    // Tür ekleme işlemi
    const turEkleForm = document.getElementById('turEkleForm');
    if (turEkleForm) {
        turEkleForm.onsubmit = async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            try {
                const response = await fetch('/tur/ekle', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Tür seçim listesini güncelle
                    const turSelect = document.getElementById('tur_select');
                    if (turSelect) {
                        const option = document.createElement('option');
                        option.value = data.tur.id;
                        option.textContent = data.tur.ad;
                        turSelect.appendChild(option);
                    }
                    
                    // Başarı mesajı göster
                    Swal.fire({
                        title: 'Başarılı!',
                        text: data.message,
                        icon: 'success',
                        timer: 1500,
                        showConfirmButton: false
                    });
                    
                    // Formu temizle
                    this.reset();
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                Swal.fire({
                    title: 'Hata!',
                    text: error.message || 'Tür eklenirken bir hata oluştu.',
                    icon: 'error',
                    confirmButtonText: 'Tamam'
                });
            }
        };
    }

    // Stok silme işlemi
    const stokSilButtons = document.querySelectorAll('.stok-sil-btn');
    stokSilButtons.forEach(button => {
        button.onclick = async function(e) {
            e.preventDefault();
            
            const id = this.getAttribute('data-id');
            if (!id) return;
            
            const result = await Swal.fire({
                title: 'Emin misiniz?',
                text: 'Bu stoğu silmek istediğinizden emin misiniz?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Evet, Sil',
                cancelButtonText: 'İptal'
            });
            
            if (result.isConfirmed) {
                try {
                    const response = await fetch(`/stok/sil/${id}`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        // Satırı kaldır
                        const row = this.closest('tr');
                        if (row) {
                            row.style.transition = 'opacity 0.3s ease';
                            row.style.opacity = '0';
                            setTimeout(() => row.remove(), 300);
                        }
                        
                        Swal.fire({
                            title: 'Başarılı!',
                            text: 'Stok başarıyla silindi.',
                            icon: 'success',
                            timer: 1500,
                            showConfirmButton: false
                        });
                    } else {
                        throw new Error('Silme işlemi başarısız oldu');
                    }
                } catch (error) {
                    Swal.fire({
                        title: 'Hata!',
                        text: error.message || 'Stok silinirken bir hata oluştu.',
                        icon: 'error',
                        confirmButtonText: 'Tamam'
                    });
                }
            }
        };
    });
}); 