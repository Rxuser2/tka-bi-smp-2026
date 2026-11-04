# Ts Sick Boii · TKA Practice Lab

**Live:** https://rxuser2.github.io/tka-bi-smp-2026/

Situs latihan CBT mandiri untuk SMP/MTs. Tema **meme Mr. Robot** memakai tampilan terminal hijau, ilustrasi dan meme orisinal; tombol **Tema klasik / Mr. Robot** mengembalikan tampilan biru-violet. Kedua tema mendukung mode siang/malam. Ukuran teks, navigasi nomor, penanda ragu-ragu, timer, autosave, skor, dan pembahasan tetap tersedia. Tidak ada jawaban yang dikirim ke server.

## Paket

| Paket | Berkas | Isi |
|---|---|---|
| Matematika · Orisinal | [Ts_Sick_Boii_Matematika.html](Ts_Sick_Boii_Matematika.html) | 10 soal lengkap dari yoo.txt, seluruhnya dinilai, 20 menit latihan |
| Matematika · Salinan identik | [Ts_Sick_Boii_Matematika_Modifikasi.html](Ts_Sick_Boii_Matematika_Modifikasi.html) | Soal dan kunci identik; URL lama Modifikasi dipertahankan |
| Final Boss · Bahasa Indonesia | [Simulasi_Interaktif_TKA_BI_SMP_2026_Final_Boss.html](Simulasi_Interaktif_TKA_BI_SMP_2026_Final_Boss.html) | 30 soal, 75 menit, 10 foto Wikimedia Commons |
| Paket 1 · Bahasa Indonesia | [Simulasi_Interaktif_TKA_BI_SMP_2026.html](Simulasi_Interaktif_TKA_BI_SMP_2026.html) | 30 soal, 75 menit, 10 bacaan bergambar |
| Paket 2 · Bahasa Indonesia | [Simulasi_Interaktif_TKA_BI_SMP_2026_Paket_2.html](Simulasi_Interaktif_TKA_BI_SMP_2026_Paket_2.html) | 30 soal berbeda, 75 menit, 10 bacaan bergambar |

Isi, gambar, kunci, pembahasan, dan revision key ketiga paket Bahasa Indonesia dipertahankan. Saved attempt lama tetap kompatibel.

## Audit salinan Matematika

[Soal dan pembahasan per nomor](analisis-soal-ts-sick-boii.html) memakai **[yoo.txt](sources/yoo.txt) sebagai satu-satunya sumber**. Sumber lama tidak digunakan.

- Kesepuluh wacana, pertanyaan, dan seluruh 49 pilihan jawaban mengikuti teks sumber, termasuk tanda baca, angka, urutan, dan kunci.
- Nomor 2 mempunyai opsi C–E `144 m²`, `154 m²`, `160 m²`; nomor 4 mempunyai opsi E `780 kursi`.
- Nomor 6 kini lengkap: `50 menit`, `60 menit`, `70 menit`, `80 menit`, `90 menit`. Kunci C dan nomor ini ikut dinilai pada kedua tautan.
- Nomor 7 memakai tepat 20 nilai dari sumber: modus 80, median 82,5.
- Rumus nomor 9 tetap `h(t) = 40t - 5t²`, sesuai tanda minus pada sumber.
- Nomor 10 mempertahankan paragraf alokasi asli tanpa grafik tambahan yang membocorkan nominal jawaban. Kunci `opt1, opt2, opt4` dipetakan ke A, B, D untuk penskoran. Semua kunci harus dipilih tanpa pilihan tambahan.
- Kunci sesuai perhitungan: C, A, C, C, B, C, C, D, C, lalu opt1/opt2/opt4. Tidak ada soal yang dikecualikan atau pilihan rekonstruksi.
- Durasi 20 menit adalah pilihan latihan situs, bukan durasi resmi sumber.

Hash sumber tersedia di [source-manifest.json](source-manifest.json). Data [orisinal](data-matematika.json), [salinan identik](data-matematika-modifikasi.json), dan [audit kunci](key-audit.json) tersedia terpisah. JSON tertanam pada kedua HTML ujian disinkronkan dengan data tersebut. Kunci browser Matematika diperbarui agar sesi lama dengan pilihan yang salah tidak dipulihkan. Data sesi Bahasa Indonesia tidak berubah.

## PDF soal dan pembahasan

[Unduh PDF revisi — 5 halaman](Ts_Sick_Boii_Matematika_Soal_dan_Pembahasan.pdf): 10 soal lengkap, seluruh pilihan, kunci, dan pembahasan dari yoo.txt. Tidak ada latihan tambahan atau lampiran sumber lama. [Lembar HTML cetak](matematika-soal-dan-pembahasan.html) memuat satu salinan soal yang sama.

## Sinkronisasi dan pengujian Matematika

Python 3.10+ dan Node.js 18+; tidak membutuhkan paket tambahan.

```bash
python scripts/sync_math.py
python scripts/sync_math.py --check
python scripts/test_math.py
node scripts/test_math_engine.cjs
```

Sinkronisasi hanya menyentuh artefak Matematika. Pengujian memeriksa kesamaan teks sumber, JSON eksternal dan tertanam, lembar audit/cetak, kunci, penilaian PG/PGK, pemulihan sesi, serta hash ketiga paket Bahasa Indonesia. PDF revisi dipertahankan sebagai artefak terverifikasi; script sinkronisasi tidak membuat ulang PDF.

## Penggunaan offline

Unduh HTML paket dan buka langsung. Masing-masing halaman ujian menyertakan seluruh teks, CSS, JavaScript, gambar, serta tema Mr. Robot. Untuk berpindah paket, melihat audit, dan membuka PDF, letakkan semua berkas unduhan pada folder yang sama.

## Sumber Bahasa Indonesia dan foto

- Kerangka publik [TKA SMP/MTs — Bahasa Indonesia](https://pusmendik.kemendikdasmen.go.id/tka/kerangka/smp/?jenis=mata-pelajaran-wajib&mapel=bahasa-indonesia) dan [Kepmendikdasmen Nomor 56 Tahun 2026](https://pusmendik.kemendikdasmen.go.id/tka/files/39870.pdf).
- Pola soal merujuk dokumen *SOAL TKA SMP SANTO YUSUP 2025* yang disediakan pengguna.
- Foto Final Boss berasal dari Wikimedia Commons; penulis, lisensi, dan tautan asli tetap dicantumkan di takarir serta bagian Tentang paket.
- Tokoh, data, dan situasi dalam paket Bahasa Indonesia merupakan fiksi atau simulasi.

Ts Sick Boii adalah situs latihan mandiri, bukan situs resmi TKA. Skor dihitung 1 poin per nomor yang benar seluruhnya, bukan skor TKA resmi.
