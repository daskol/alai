FROM archlinux:base-devel

RUN --mount=type=cache,target=/var/cache/pacman,sharing=locked \
    --mount=type=cache,target=/var/lib/pacman/sync,sharing=locked \
    pacman -Sy --noconfirm clang cmake ninja python python-build

WORKDIR /usr/src/alai

ADD . .

RUN cmake -S . -B build -G 'Ninja Multi-Config' \
        -DCMAKE_CXX_COMPILER=clang++ \
        -DENABLE_TESTS=OFF && \
    cmake --build build --config Release -t extension && \
    cp build/alai/Release/extension.cpython-313-x86_64-linux-gnu.so alai && \
    rm -rf build
