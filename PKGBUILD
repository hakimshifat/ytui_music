# Maintainer: Shifat <hakim.shifat@gmail.com>
# Contributor: Abdul Hakim Shifat

pkgname=ytui_music
pkgver=0.1.0
pkgrel=1
pkgdesc="A terminal-based YouTube audio player built with Textual and mpv"
arch=('any')
url="https://github.com/hakimshifat/ytui_music"
license=('GPL-3.0-or-later')
depends=(
    'python'
    'mpv'
    'python-textual'
    'python-textual-image'
    'python-yt-dlp'
    'python-requests'
    'python-mpv'
    'python-pillow'
    'python-rich'
    'python-markdown-it-py'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-setuptools'
)
source=("$pkgname-$pkgver.tar.gz::https://github.com/hakimshifat/ytui_music/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('abbcb37c244fdcb1e69cf050e59a45cd3392536cdc473a3401d225153d3699a0')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Install only the main package (dependencies from Arch repos)
    pip install --root="$pkgdir" --ignore-installed --no-deps --no-build-isolation \
        --no-warn-script-location dist/*.whl 2>/dev/null
    
    # Ensure the script is executable
    install -Dm755 yt.py "$pkgdir/usr/bin/ytui_music"
}
