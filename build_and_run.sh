echo "attemption to build and run"
pip install -r requirements.txt
cargo build --release --manifest-path=./iron_brains/Cargo.toml
cp iron_brains/target/release/libiron_brains.so ./brains/iron_brains.so
cp iron_brains/target/release/libiron_brains.d ./brains/iron_brains.d
python brains/main.py --world=easy --display=pygame --epochs=5000
