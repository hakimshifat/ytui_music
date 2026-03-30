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
sha256sums=('3680696b06a5f5482e8863387a2b319a4c72c2879f13a2bedee4e898698c0cda')

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
