#!/usr/bin/env python3
"""
印象笔记到Obsidian迁移工具 - Web界面
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import tempfile
import threading
import uuid

from flask import Flask, render_template, request, jsonify, session, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import colorama

# 添加src目录到Python路径
src_dir = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_dir))

from config import Config
from desktop_api import preflight_config
from unified_migrator import UnifiedMigrator


class WebMigrator:
    """Web界面迁移器"""

    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'evernote_obsidian_migration_2024'
        desktop_origins = ['null', 'http://localhost:5173', 'http://127.0.0.1:5173']
        desktop_mode = os.environ.get('EVERNOTE_DESKTOP_MODE') == '1'
        if desktop_mode:
            CORS(self.app, resources={r'/api/*': {'origins': desktop_origins}})
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins=desktop_origins if desktop_mode else '*',
        )

        # 存储活跃的迁移任务
        self.active_migrations = {}
        self.cancel_events = {}

        self.setup_routes()
        self.setup_socketio_events()

    def setup_routes(self):
        """设置路由"""

        @self.app.route('/api/healthz')
        def healthz():
            return jsonify({'status': 'ok'})

        @self.app.route('/api/preflight', methods=['POST'])
        def preflight():
            result = preflight_config(request.get_json(silent=True))
            return jsonify(result), 200 if result['ok'] else 422

        @self.app.route('/')
        def index():
            """主页"""
            return render_template('index.html')

        @self.app.route('/config')
        def config_page():
            """配置页面"""
            return render_template('config.html')

        @self.app.route('/migrate')
        def migrate_page():
            """迁移页面"""
            return render_template('migrate.html')

        @self.app.route('/results')
        def results_page():
            """结果页面"""
            return render_template('results.html')

        @self.app.route('/api/start_migration', methods=['POST'])
        def start_migration():
            """开始迁移"""
            try:
                print(f"收到迁移请求")
                config_data = request.get_json()
                print(f"配置数据: {config_data}")

                if not config_data:
                    return jsonify({
                        'success': False,
                        'error': '没有接收到配置数据'
                    })

                # 生成唯一的任务ID
                task_id = str(uuid.uuid4())
                session['task_id'] = task_id
                print(f"生成任务ID: {task_id}")
                self.cancel_events[task_id] = threading.Event()

                # 创建配置对象
                config = Config()
                config.config_data = config_data

                # 在后台线程中运行迁移
                migration_thread = threading.Thread(
                    target=self._run_migration_task,
                    args=(task_id, config)
                )
                migration_thread.daemon = True
                migration_thread.start()

                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': '迁移任务已开始'
                })

            except Exception as e:
                print(f"迁移启动错误: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/start_export', methods=['POST'])
        def start_export():
            """开始导出ENEX文件"""
            try:
                print(f"收到迁移请求")
                config_data = request.get_json()
                print(f"配置数据: {config_data}")

                if not config_data:
                    return jsonify({
                        'success': False,
                        'error': '没有接收到配置数据'
                    })

                # 生成唯一的任务ID
                task_id = str(uuid.uuid4())
                session['task_id'] = task_id
                print(f"生成任务ID: {task_id}")

                # 获取导出目录并处理
                export_dir = config_data.get('output', {}).get('enex_directory', '/tmp/evernote_export')
                
                # 处理Mac系统下的'~'路径
                if export_dir.startswith('~'):
                    export_dir = os.path.expanduser(export_dir)
                
                # 创建导出目录（如果不存在）
                Path(export_dir).mkdir(parents=True, exist_ok=True)
                print(f"创建导出目录: {export_dir}")
                
                # 创建配置对象
                config = Config()
                # 设置输出目录
                config.set('output.enex_directory', export_dir)
                # 设置印象笔记配置
                config.set('evernote_backend', config_data.get('evernote_backend', 'china'))
                config.set('evernote_credentials', config_data.get('evernote_credentials', {}))

                # 在后台线程中运行导出
                export_thread = threading.Thread(
                    target=self._run_export_task,
                    args=(task_id, config)
                )
                export_thread.daemon = True
                export_thread.start()

                return jsonify({
                    'success': True,
                    'task_id': task_id,
                    'message': '导出任务已开始'
                })

            except Exception as e:
                print(f"导出启动错误: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/export_enex', methods=['POST'])
        def export_enex():
            """导出ENEX文件（简化版本）"""
            try:
                print(f"收到导出ENEX请求")
                config_data = request.get_json()
                print(f"配置数据: {config_data}")

                if not config_data:
                    return jsonify({
                        'success': False,
                        'error': '没有接收到配置数据'
                    })

                # 生成唯一的任务ID
                task_id = str(uuid.uuid4())
                session['task_id'] = task_id
                print(f"生成任务ID: {task_id}")

                # 获取导出目录并处理
                export_dir = config_data.get('output', {}).get('enex_directory', '/tmp/evernote_export')
                
                # 处理Mac系统下的'~'路径
                if export_dir.startswith('~'):
                    export_dir = os.path.expanduser(export_dir)
                
                # 创建导出目录（如果不存在）
                from pathlib import Path
                Path(export_dir).mkdir(parents=True, exist_ok=True)
                print(f"创建导出目录: {export_dir}")
                
                # 创建配置对象
                config = Config()
                # 设置输出目录
                config.set('output.enex_directory', export_dir)
                # 设置印象笔记配置
                config.set('evernote_backend', config_data.get('evernote_backend', 'china'))
                config.set('evernote_credentials', config_data.get('evernote_credentials', {}))

                # 导入必要的模块
                from evernote_exporter import EvernoteExporter
                import shutil
                
                # 创建导出器并执行导出
                exporter = EvernoteExporter(config.get_all())
                
                # 检查依赖
                if not exporter.check_dependencies():
                    return jsonify({
                        'success': False,
                        'error': '依赖检查失败'
                    })
                
                # 执行导出
                enex_files = exporter.export_notes()
                
                if not enex_files:
                    return jsonify({
                        'success': False,
                        'error': '没有导出任何ENEX文件'
                    })
                
                # 将导出的ENEX文件复制到用户指定的目录
                copied_files = []
                for enex_file in enex_files:
                    source_file = Path(enex_file)
                    dest_file = Path(export_dir) / source_file.name
                    
                    try:
                        shutil.copy2(source_file, dest_file)
                        copied_files.append(str(dest_file))
                        print(f"📋 复制ENEX文件: {source_file.name} -> {dest_file}")
                    except Exception as e:
                        print(f"❌ 复制ENEX文件失败: {e}")
                
                return jsonify({
                    'success': True,
                    'message': 'ENEX导出成功',
                    'enex_files': copied_files,
                    'export_dir': export_dir
                })

            except Exception as e:
                print(f"导出错误: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

        @self.app.route('/api/migration_status/<task_id>')
        def migration_status(task_id):
            """获取迁移状态"""
            if task_id in self.active_migrations:
                return jsonify(self.active_migrations[task_id])
            else:
                return jsonify({
                    'status': 'not_found',
                    'message': '任务未找到'
                })

        @self.app.route('/api/cancel_migration/<task_id>', methods=['POST'])
        def cancel_migration(task_id):
            if task_id not in self.active_migrations and task_id not in self.cancel_events:
                return jsonify({'status': 'not_found', 'task_id': task_id}), 404
            self.cancel_events.setdefault(task_id, threading.Event()).set()
            return jsonify({'task_id': task_id, 'status': 'cancelling'})

        @self.app.route('/api/upload_enex', methods=['POST'])
        def upload_enex():
            """上传ENEX文件"""
            try:
                uploaded_files = request.files.getlist('enex_files')

                if not uploaded_files:
                    return jsonify({
                        'success': False,
                        'error': '没有选择文件'
                    })

                # 创建临时目录
                temp_dir = tempfile.mkdtemp(prefix='enex_upload_')
                saved_files = []

                for file in uploaded_files:
                    if file.filename and file.filename.endswith('.enex'):
                        file_path = Path(temp_dir) / file.filename
                        file.save(str(file_path))
                        saved_files.append(str(file_path))

                return jsonify({
                    'success': True,
                    'files': saved_files,
                    'temp_dir': temp_dir
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                })

    def setup_socketio_events(self):
        """设置WebSocket事件"""

        @self.socketio.on('connect')
        def handle_connect():
            print(f"客户端已连接: {request.sid}")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print(f"客户端已断开: {request.sid}")

        @self.socketio.on('join_task')
        def handle_join_task(data):
            """加入任务房间"""
            task_id = data.get('task_id')
            if task_id:
                from flask_socketio import join_room
                join_room(task_id)
                print(f"客户端 {request.sid} 加入任务 {task_id}")

    def _run_migration_task(self, task_id: str, config: Config):
        """在后台运行迁移任务"""
        try:
            print(f"🚀 开始迁移任务 {task_id}")
            cancel_event = self.cancel_events.setdefault(task_id, threading.Event())

            # 初始化任务状态
            self.active_migrations[task_id] = {
                'status': 'running',
                'step': 1,
                'total_steps': 4,
                'current_step_name': '导出印象笔记',
                'progress': 0,
                'message': '正在开始迁移...',
                'start_time': datetime.now().isoformat(),
                'stats': {
                    'total_notes': 0,
                    'converted_notes': 0,
                    'total_attachments': 0,
                    'errors': []
                }
            }

            print(f"📊 初始化任务状态: {self.active_migrations[task_id]}")

            # 发送初始进度更新
            self.socketio.emit('migration_progress', {
                'task_id': task_id,
                'step': 1,
                'step_name': '导出印象笔记',
                'progress': 0,
                'message': '正在开始迁移...'
            }, room=task_id)

            # 创建自定义迁移器
            print(f"🔧 创建迁移处理器...")
            migrator = WebMigrationHandler(
                task_id, self.socketio, self.active_migrations, cancel_event,
            )
            migrator.config = config

            print(f"📝 配置信息: {config.get_all()}")

            # 运行迁移
            print(f"▶️  开始执行迁移...")
            success = migrator.run_migration()
            print(f"✅ 迁移完成，结果: {success}")

            # 更新最终状态
            if cancel_event.is_set():
                self.active_migrations[task_id].update({
                    'status': 'cancelled',
                    'end_time': datetime.now().isoformat(),
                    'message': '迁移已取消，已写入的文件不会回滚'
                })
                self.socketio.emit('migration_cancelled', {'task_id': task_id}, room=task_id)
            else:
                self.active_migrations[task_id].update({
                    'status': 'completed' if success else 'failed',
                    'progress': 100,
                    'end_time': datetime.now().isoformat(),
                    'message': '迁移完成!' if success else '迁移失败'
                })

                # 发送完成事件
                self.socketio.emit('migration_completed', {
                    'task_id': task_id,
                    'success': success,
                    'result': self.active_migrations[task_id]
                }, room=task_id)

        except Exception as e:
            print(f"❌ 迁移任务错误: {e}")
            import traceback
            traceback.print_exc()

            self.active_migrations[task_id].update({
                'status': 'failed',
                'message': f'迁移错误: {str(e)}',
                'end_time': datetime.now().isoformat()
            })

            self.socketio.emit('migration_error', {
                'task_id': task_id,
                'error': str(e)
            }, room=task_id)
            
    def _run_export_task(self, task_id: str, config: Config):
        """在后台运行导出ENEX任务"""
        try:
            print(f"🚀 开始导出ENEX任务 {task_id}")

            # 初始化任务状态
            self.active_migrations[task_id] = {
                'status': 'running',
                'progress': 0,
                'message': '正在开始导出...',
                'start_time': datetime.now().isoformat(),
                'stats': {
                    'total_notes': 0,
                    'exported_files': [],
                    'errors': []
                }
            }

            print(f"📊 初始化任务状态: {self.active_migrations[task_id]}")

            # 发送初始进度更新
            self.socketio.emit('export_progress', {
                'task_id': task_id,
                'progress': 0,
                'message': '正在开始导出...'
            }, room=task_id)

            # 导入必要的模块
            from evernote_exporter import EvernoteExporter

            # 发送进度更新
            self.socketio.emit('export_progress', {
                'task_id': task_id,
                'progress': 10,
                'message': '正在检查依赖...'
            }, room=task_id)
            
            # 创建导出器
            exporter = EvernoteExporter(config.get_all())
            
            # 检查依赖
            if not exporter.check_dependencies():
                self.active_migrations[task_id].update({
                    'status': 'failed',
                    'message': '依赖检查失败'
                })
                self.socketio.emit('export_error', {
                    'task_id': task_id,
                    'error': '依赖检查失败'
                }, room=task_id)
                return
            
            # 发送进度更新
            self.socketio.emit('export_progress', {
                'task_id': task_id,
                'progress': 30,
                'message': '正在初始化导出器...'
            }, room=task_id)
            
            # 执行导出
            self.socketio.emit('export_progress', {
                'task_id': task_id,
                'progress': 50,
                'message': '正在导出笔记数据...'
            }, room=task_id)
            
            enex_files = exporter.export_notes()
            
            if not enex_files:
                self.active_migrations[task_id].update({
                    'status': 'failed',
                    'message': '没有导出任何ENEX文件'
                })
                self.socketio.emit('export_error', {
                    'task_id': task_id,
                    'error': '没有导出任何ENEX文件'
                }, room=task_id)
                return
            
            # 发送进度更新
            self.socketio.emit('export_progress', {
                'task_id': task_id,
                'progress': 80,
                'message': f'正在保存ENEX文件...'
            }, room=task_id)
            
            # 更新任务状态
            self.active_migrations[task_id].update({
                'status': 'completed',
                'progress': 100,
                'message': '导出完成',
                'end_time': datetime.now().isoformat(),
                'stats': {
                    'total_notes': sum(len(exporter._parse_enex_file(f)) for f in enex_files),
                    'exported_files': enex_files
                }
            })
            
            # 发送完成事件
            self.socketio.emit('export_completed', {
                'task_id': task_id,
                'success': True,
                'enex_path': enex_files[0] if enex_files else '',
                'result': self.active_migrations[task_id]
            }, room=task_id)
            
        except Exception as e:
            print(f"❌ 导出任务错误: {e}")
            import traceback
            traceback.print_exc()
            
            self.active_migrations[task_id].update({
                'status': 'failed',
                'message': f'导出错误: {str(e)}',
                'end_time': datetime.now().isoformat()
            })
            
            self.socketio.emit('export_error', {
                'task_id': task_id,
                'error': str(e)
            }, room=task_id)

    def run(self, host='127.0.0.1', port=5000, debug=False,
            allow_unsafe_werkzeug=False):
        """运行Web应用"""
        print(f"🌐 启动Web界面: http://{host}:{port}")
        self.socketio.run(
            self.app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=allow_unsafe_werkzeug,
        )


class WebMigrationHandler(UnifiedMigrator):
    """Web界面专用的迁移处理器"""

    def __init__(self, task_id: str, socketio, active_migrations: dict,
                 cancel_event: threading.Event | None = None):
        super().__init__()
        self.task_id = task_id
        self.socketio = socketio
        self.active_migrations = active_migrations
        self.cancel_event = cancel_event or threading.Event()

    def _is_cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def _emit_progress(self, step: int, step_name: str, progress: int, message: str):
        """发送进度更新"""
        print(f"📈 进度更新: 步骤{step} - {step_name} ({progress}%) - {message}")

        self.active_migrations[self.task_id].update({
            'step': step,
            'current_step_name': step_name,
            'progress': progress,
            'message': message
        })

        progress_data = {
            'task_id': self.task_id,
            'step': step,
            'step_name': step_name,
            'progress': progress,
            'message': message
        }

        print(f"📤 发送进度数据: {progress_data}")

        self.socketio.emit('migration_progress', progress_data, room=self.task_id)

    def _step_export_evernote(self) -> bool:
        """步骤1：导出印象笔记（重写以支持Web进度）"""
        self._emit_progress(1, '导出印象笔记', 10, '正在检查依赖...')

        try:
            from evernote_exporter import EvernoteExporter

            self._emit_progress(1, '导出印象笔记', 20, '正在初始化导出器...')
            exporter = EvernoteExporter(self.config.get_all())

            if not exporter.check_dependencies():
                self._emit_progress(1, '导出印象笔记', 0, '依赖检查失败')
                return False

            self._emit_progress(1, '导出印象笔记', 50, '正在导出笔记数据...')
            enex_files = exporter.export_notes()

            if not enex_files:
                self._emit_progress(1, '导出印象笔记', 0, '没有导出任何文件')
                return False

            self.config.set('input.enex_files', enex_files)
            self._emit_progress(1, '导出印象笔记', 100, f'导出完成，共 {len(enex_files)} 个文件')
            return True

        except Exception as e:
            self._emit_progress(1, '导出印象笔记', 0, f'导出失败: {e}')
            return False

    def _step_convert_to_markdown(self) -> bool:
        """步骤2：转换为Markdown（重写以支持Web进度）"""
        self._emit_progress(2, '转换为Markdown', 10, '正在初始化转换器...')

        try:
            from enex_parser import ENEXParser
            from markdown_converter import MarkdownConverter
            from file_organizer import FileOrganizer

            parser = ENEXParser()
            converter = MarkdownConverter(self.config.get_all())
            organizer = FileOrganizer(self.config.get_all())

            enex_files = self.config.get('input.enex_files', [])
            total_notes = 0
            converted_notes = 0

            self._emit_progress(2, '转换为Markdown', 20, f'开始处理 {len(enex_files)} 个文件...')

            for i, enex_file in enumerate(enex_files):
                if self._is_cancelled():
                    return False
                try:
                    progress = 20 + (i * 60 // len(enex_files))
                    self._emit_progress(2, '转换为Markdown', progress, f'处理文件: {Path(enex_file).name}')

                    notes, notebook_name = parser.parse_file(enex_file)
                    total_notes += len(notes)

                    organized_notes = organizer.organize_notes(notes, notebook_name)
                    organizer.create_directory_structure(organized_notes)

                    for note, file_path in organized_notes:
                        try:
                            markdown_content = converter.convert_note(note)
                            organizer.save_note(note, file_path, markdown_content)

                            if note.attachments:
                                organizer.save_attachments(note)
                                self.stats['total_attachments'] += len(note.attachments)

                            converted_notes += 1

                        except Exception as e:
                            self.stats['skipped_notes'] += 1

                    organizer.create_index_file(organized_notes, notebook_name)

                except Exception as e:
                    self._emit_progress(2, '转换为Markdown', progress, f'跳过文件: {e}')

            self.stats['total_notes'] = total_notes
            self.stats['converted_notes'] = converted_notes

            self._emit_progress(2, '转换为Markdown', 100,
                              f'转换完成: {converted_notes}/{total_notes} 个笔记')
            return converted_notes > 0

        except Exception as e:
            self._emit_progress(2, '转换为Markdown', 0, f'转换失败: {e}')
            return False

    def _step_setup_obsidian(self) -> bool:
        """步骤3：设置Obsidian库（重写以支持Web进度）"""
        self._emit_progress(3, '设置Obsidian库', 10, '正在初始化Obsidian管理器...')

        try:
            from obsidian_manager import ObsidianManager

            # 设置迁移信息
            self.config.set('migration_time', self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S'))
            self.config.set('total_notes', self.stats['total_notes'])
            self.config.set('converted_notes', self.stats['converted_notes'])

            obsidian_manager = ObsidianManager(self.config.get_all())

            self._emit_progress(3, '设置Obsidian库', 25, '正在创建库结构...')
            if not obsidian_manager.create_obsidian_vault():
                return False

            self._emit_progress(3, '设置Obsidian库', 50, '正在创建欢迎笔记...')
            if self.config.get('migration.create_welcome_note', True):
                obsidian_manager.create_welcome_note()

            self._emit_progress(3, '设置Obsidian库', 75, '正在创建模板...')
            if self.config.get('migration.create_templates', True):
                obsidian_manager.create_templates()

            self._emit_progress(3, '设置Obsidian库', 90, '正在优化设置...')
            if self.config.get('migration.optimize_settings', True):
                obsidian_manager.optimize_vault_settings()

            obsidian_manager.install_recommended_plugins()

            self._emit_progress(3, '设置Obsidian库', 100, 'Obsidian库设置完成')
            return True

        except Exception as e:
            self._emit_progress(3, '设置Obsidian库', 0, f'库设置失败: {e}')
            return False

    def _step_post_process(self) -> bool:
        """步骤4：后处理（重写以支持Web进度）"""
        self._emit_progress(4, '完成后处理', 25, '正在清理临时文件...')

        try:
            if not self.config.get('migration.keep_temp_files', False):
                self._cleanup_temp_files()

            self._emit_progress(4, '完成后处理', 75, '正在准备启动Obsidian...')

            vault_path = self.config.get('output.obsidian_vault')
            self._emit_progress(4, '完成后处理', 100, f'迁移完成! 库位置: {vault_path}')

            return True

        except Exception as e:
            self._emit_progress(4, '完成后处理', 50, f'后处理警告: {e}')
            return True

    def run_migration(self) -> bool:
        """运行迁移流程，支持跳过导出步骤"""
        print(f"🚀 开始迁移流程...")

        # 初始化开始时间
        from datetime import datetime
        self.stats['start_time'] = datetime.now()

        if self._is_cancelled():
            return False

        # 检查是否有已上传的ENEX文件
        uploaded_files = self.config.get('input.enex_files', [])

        if uploaded_files:
            print(f"📁 检测到已上传的ENEX文件: {len(uploaded_files)} 个")
            # 跳过导出步骤，直接进行转换
            self._emit_progress(1, '导出印象笔记', 100, '使用已上传的ENEX文件')

            # 直接进行转换
            if not self._step_convert_to_markdown():
                return False
        else:
            # 正常流程：先导出再转换
            if not self._step_export_evernote():
                return False

            if self._is_cancelled():
                return False
            if not self._step_convert_to_markdown():
                return False

        if self._is_cancelled():
            return False
        if not self._step_setup_obsidian():
            return False

        if self._is_cancelled():
            return False
        if not self._step_post_process():
            return False

        return True


if __name__ == '__main__':
    colorama.init(autoreset=True)

    web_migrator = WebMigrator()
    web_migrator.run(host='0.0.0.0', port=5000, debug=True)
