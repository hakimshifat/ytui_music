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
)
makedepends=(
    'python-build'
    'python-installer'
    'python-setuptools'
)
source=("$pkgname-$pkgver.tar.gz::https://github.com/hakimshifat/ytui_music/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('7c3973b0975f4ed67fe5396ba5b810007106df8affb3533add9302023cd71f69')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Install the Python package with dependencies (suppress pip warnings)
    pip install --root="$pkgdir" --ignore-installed --no-build-isolation \
        --no-warn-script-location dist/*.whl 2>/dev/null
    
    # Ensure the script is executable
    install -Dm755 yt.py "$pkgdir/usr/bin/ytui_music"
}
