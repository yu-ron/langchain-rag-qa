"""
数据库初始化脚本
首次运行项目时执行，自动建表并创建管理员账号
用法：python init_db.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import sync_engine, Base, SyncSessionLocal
from app.models.user import User
from app.core.security import hash_password
from app.core.config import ADMIN_USERNAME, ADMIN_PASSWORD, UPLOAD_DIR


def init_database():
    """初始化数据库：建表 + 创建管理员账号"""
    print("[INFO] 正在初始化数据库...")

    # 1. 创建所有表
    Base.metadata.create_all(bind=sync_engine)
    print("[OK] 数据库表创建完成")

    # 2. 创建上传目录
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("chroma_data", exist_ok=True)
    print(f"[OK] 上传目录创建完成: {UPLOAD_DIR}")

    # 3. 检查管理员账号是否已存在
    db = SyncSessionLocal()
    try:
        existing_admin = db.query(User).filter(
            User.username == ADMIN_USERNAME
        ).first()

        if existing_admin:
            print(f"[INFO] 管理员账号已存在: {ADMIN_USERNAME}")
        else:
            # 创建管理员
            admin = User(
                username=ADMIN_USERNAME,
                password_hash=hash_password(ADMIN_PASSWORD),
                role="admin",
            )
            db.add(admin)
            db.commit()
            print(f"[OK] 管理员账号创建成功")
            print(f"     用户名: {ADMIN_USERNAME}")
            print(f"     密码: {ADMIN_PASSWORD}")
            print(f"     *** 请登录后立即修改默认密码！***")

        # 4. 显示统计信息
        user_count = db.query(User).count()
        print(f"\n[INFO] 统计信息:")
        print(f"   用户总数: {user_count}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 初始化失败: {e}")
        raise
    finally:
        db.close()

    print("\n[OK] 数据库初始化完成！")
    print("   运行 python main.py 启动后端服务")
    print("   然后访问 http://localhost:8000/docs 查看 API 文档")


if __name__ == "__main__":
    init_database()
