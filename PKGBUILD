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
sha256sums=('4a9e76f58d5c00fc06b3ec9b3800e7362de4866a3230fc98163d6ebe1e3ee868')

build() {
    cd "$srcdir/$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$srcdir/$pkgname-$pkgver"
    
    # Install the Python package with dependencies
    pip install --root="$pkgdir" --ignore-installed --no-build-isolation dist/*.whl
    
    # Ensure the script is executable
    install -Dm755 yt.py "$pkgdir/usr/bin/ytui_music"
}
