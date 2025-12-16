"""
カメラ自動検出モジュール
ネットワーク上でカメラサーバーを自動検出
"""
import socket
import threading
import time
from typing import List, Dict, Optional, Callable
import subprocess
import platform
import json
import concurrent.futures
import os

# requestsライブラリのインポート（オプション）
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("警告: requestsがインストールされていません。HTTPベースの検出は使用できません。")
    print("インストール: pip install requests")

def scan_port(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    指定されたホストとポートが開いているかチェック
    
    Args:
        host: ホスト名またはIPアドレス
        port: ポート番号
        timeout: タイムアウト（秒）
    
    Returns:
        ポートが開いていればTrue
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def get_local_ip() -> str:
    """
    ローカルIPアドレスを取得
    
    Returns:
        ローカルIPアドレス
    """
    try:
        # 外部サーバーに接続してローカルIPを取得
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def get_network_range(ip: str) -> List[str]:
    """
    IPアドレスからネットワーク範囲を取得
    
    Args:
        ip: IPアドレス（例: "192.168.1.100"）
    
    Returns:
        ネットワーク範囲のIPアドレスリスト
    """
    parts = ip.split('.')
    if len(parts) != 4:
        return []
    
    base = '.'.join(parts[:3])
    # 一般的なローカルネットワーク範囲（1-254）
    return [f"{base}.{i}" for i in range(1, 255)]

def get_all_network_ranges(include_common: bool = True) -> List[str]:
    """
    すべてのローカルネットワーク範囲を取得
    親機のIPアドレスだけでなく、一般的なローカルネットワーク範囲もスキャン
    
    Args:
        include_common: 一般的なネットワーク範囲も含めるか（デフォルト: True）
    
    Returns:
        ネットワーク範囲のIPアドレスリスト（重複除去済み）
    """
    all_ips = []
    
    # 1. 親機のローカルIPからネットワーク範囲を取得
    local_ip = get_local_ip()
    if local_ip and local_ip != "127.0.0.1":
        network_range = get_network_range(local_ip)
        all_ips.extend(network_range)
        network_base = local_ip.rsplit('.', 1)[0]
        print(f"親機のネットワーク範囲を追加: {network_base}.0/24 ({len(network_range)}個のIP)")
    
    # 2. 一般的なローカルネットワーク範囲も追加（異なるサブネットの可能性に対応）
    if include_common:
        common_networks = [
            "192.168.0", "192.168.1", "192.168.2", "192.168.3",
            "10.0.0", "10.0.1", "10.0.2",
            "172.16.0", "172.16.1", "172.17.0", "172.18.0"
        ]
        
        added_networks = []
        for network_base in common_networks:
            # 親機のネットワーク範囲と重複しない場合のみ追加
            if not local_ip.startswith(network_base):
                network_range = [f"{network_base}.{i}" for i in range(1, 255)]
                all_ips.extend(network_range)
                added_networks.append(network_base)
        
        if added_networks:
            print(f"一般的なネットワーク範囲も追加: {', '.join(added_networks)}")
    
    # 重複を除去して返す
    unique_ips = list(set(all_ips))
    print(f"総スキャン対象: {len(unique_ips)}個のIPアドレス")
    return unique_ips

def discover_cameras(ports: List[int] = [5000, 5001, 5002, 5003], 
                     timeout: float = 0.5,
                     scan_localhost: bool = True) -> Dict[int, Optional[str]]:
    """
    ネットワーク上でカメラサーバーを検出
    
    Args:
        ports: スキャンするポート番号のリスト
        timeout: 各ポートのタイムアウト（秒）
        scan_localhost: localhostもスキャンするか
    
    Returns:
        ポート番号をキー、IPアドレスを値とする辞書
    """
    discovered = {}
    
    # localhostをスキャン
    if scan_localhost:
        print("localhostをスキャン中...")
        for port in ports:
            if scan_port("127.0.0.1", port, timeout):
                discovered[port] = "127.0.0.1"
                print(f"  ポート {port}: localhost で検出")
    
    # ローカルネットワークをスキャン
    local_ip = get_local_ip()
    print(f"ローカルネットワーク ({local_ip}) をスキャン中...")
    
    network_range = get_network_range(local_ip)
    
    # マルチスレッドでスキャン
    results = {}
    lock = threading.Lock()
    
    def scan_host_port(host, port):
        if scan_port(host, port, timeout):
            with lock:
                if port not in results:
                    results[port] = host
                    print(f"  ポート {port}: {host} で検出")
    
    threads = []
    for host in network_range:
        for port in ports:
            if port in discovered:
                continue  # 既に見つかったポートはスキップ
            thread = threading.Thread(target=scan_host_port, args=(host, port))
            thread.daemon = True
            thread.start()
            threads.append(thread)
            
            # スレッド数が多すぎないように制限
            if len(threads) >= 100:
                for t in threads:
                    t.join(timeout=0.1)
                threads = []
    
    # 残りのスレッドを待つ
    for thread in threads:
        thread.join(timeout=1.0)
    
    # 結果をマージ
    for port in ports:
        if port not in discovered and port in results:
            discovered[port] = results[port]
    
    return discovered

def discover_cameras_fast(ports: List[int] = [5000, 5001, 5002, 5003]) -> Dict[int, Optional[str]]:
    """
    高速なカメラ検出（localhostと現在のホストのみ）
    
    Args:
        ports: スキャンするポート番号のリスト
    
    Returns:
        ポート番号をキー、IPアドレスを値とする辞書
    """
    discovered = {}
    
    # localhostをチェック
    print("localhostをチェック中...")
    for port in ports:
        if scan_port("127.0.0.1", port, timeout=0.5):
            discovered[port] = "127.0.0.1"
            print(f"  ポート {port}: localhost で検出")
    
    # 現在のホストのIPをチェック
    local_ip = get_local_ip()
    if local_ip != "127.0.0.1":
        print(f"現在のホスト ({local_ip}) をチェック中...")
        for port in ports:
            if port not in discovered and scan_port(local_ip, port, timeout=0.5):
                discovered[port] = local_ip
                print(f"  ポート {port}: {local_ip} で検出")
    
    return discovered

def scan_single_camera_info(ip: str, port: int, timeout: float = 0.5, debug: bool = False) -> Optional[Dict]:
    """
    単一のIPアドレスとポートに対して/infoエンドポイントにアクセス
    
    Args:
        ip: スキャンするIPアドレス
        port: 子機のポート番号
        timeout: タイムアウト時間（秒）
        debug: デバッグモード（エラーを表示）
    
    Returns:
        子機情報の辞書、またはNone
    """
    if not REQUESTS_AVAILABLE:
        return None
    
    url = f"http://{ip}:{port}/info"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            # /infoが返す実際のポート番号を使用（子機が実際に使用しているポート）
            actual_port = data.get('port', port)
            actual_ip = data.get('ip_address', ip)
            return {
                'ip_address': actual_ip,
                'port': actual_port,  # 子機が実際に使用しているポート
                'camera_id': data.get('camera_id'),
                'stream_url': data.get('stream_url'),
                'status': data.get('status', 'running')
            }
        elif debug:
            print(f"  [デバッグ] {ip}:{port} - HTTPステータス: {response.status_code}")
    except requests.exceptions.Timeout:
        if debug:
            print(f"  [デバッグ] {ip}:{port} - タイムアウト")
    except requests.exceptions.ConnectionError as e:
        if debug:
            print(f"  [デバッグ] {ip}:{port} - 接続エラー: {e}")
    except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
        if debug:
            print(f"  [デバッグ] {ip}:{port} - エラー: {e}")
    return None

def discover_cameras_by_info(ports: List[int] = [5000, 5001, 5002, 5003],
                              timeout: float = 0.5,
                              max_workers: int = 50,
                              debug_ips: List[str] = None,
                              on_camera_found: Optional[Callable[[int, str], None]] = None) -> Dict[int, Optional[str]]:
    """
    /infoエンドポイントを使用してネットワーク内の子機を検出（推奨）
    複数のネットワークインターフェースに対応
    
    Args:
        ports: スキャンするポート番号のリスト
        timeout: 各リクエストのタイムアウト時間（秒）
        max_workers: 並列処理の最大ワーカー数
        debug_ips: デバッグ対象のIPアドレスリスト
        on_camera_found: カメラが見つかったときに呼び出されるコールバック関数
                        (port, ip) を引数として受け取る
    
    Returns:
        ポート番号をキー、IPアドレスを値とする辞書
    """
    if not REQUESTS_AVAILABLE:
        print("警告: requestsがインストールされていません。HTTPベースの検出をスキップします。")
        return {}
    
    # まず親機のネットワーク範囲をスキャン
    local_ip = get_local_ip()
    print(f"親機のIPアドレス: {local_ip}")
    
    # 検出結果を保存する辞書（最初に初期化）
    discovered = {}
    detected_cameras = []
    
    # 既知の子機IPアドレスがあれば、優先的にテスト（環境変数から取得可能）
    known_child_ips = os.getenv('KNOWN_CHILD_IPS', '').split(',')
    known_child_ips = [ip.strip() for ip in known_child_ips if ip.strip()]
    
    if known_child_ips:
        print(f"既知の子機IPアドレスを優先的にテスト: {known_child_ips}")
        # 既知のIPに対して、一般的なポート（5000-5004）も含めてテスト
        test_ports = list(set(ports + [5000, 5001, 5002, 5003, 5004]))
        for known_ip in known_child_ips:
            for port in test_ports:
                print(f"  テスト中: {known_ip}:{port}...")
                result = scan_single_camera_info(known_ip, port, timeout, debug=True)
                if result:
                    # /infoが返す実際のポート番号を使用
                    actual_port = result['port']  # 子機が実際に使用しているポート
                    ip_addr = result['ip_address']
                    camera_id = result.get('camera_id', 'unknown')
                    if actual_port not in discovered:
                        discovered[actual_port] = ip_addr
                        print(f"✓ 子機を検出（既知IP）: {ip_addr}:{actual_port} (カメラID: {camera_id})")
                        # 見つかったカメラを即座に通知
                        if on_camera_found:
                            on_camera_found(actual_port, ip_addr)
    
    # まず親機のネットワーク範囲のみをスキャン（高速）
    network_range = get_all_network_ranges(include_common=False)
    
    print(f"ネットワークスキャンを開始（親機のネットワーク範囲）")
    print(f"スキャンポート: {ports}")
    print(f"総スキャン数: {len(network_range) * len(ports)}")
    
    start_time = time.time()
    
    # 全IPアドレス × 全ポートの組み合わせをスキャン
    tasks = []
    for ip in network_range:
        for port in ports:
            tasks.append((ip, port))
    
    # デバッグ対象のIPアドレスリスト（指定されたIPは詳細ログを出力）
    debug_ips_set = set(debug_ips) if debug_ips else set()
    
    # 並列処理でスキャン
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {
            executor.submit(scan_single_camera_info, ip, port, timeout, ip in debug_ips_set): (ip, port)
            for ip, port in tasks
        }
        
        # 見つかったIPアドレスを追跡（同じIPの他のポートを優先スキャンするため）
        found_ips = set()
        
        for future in concurrent.futures.as_completed(future_to_task):
            result = future.result()
            if result:
                detected_cameras.append(result)
                # /infoが返す実際のポート番号を使用
                actual_port = result['port']  # 子機が実際に使用しているポート
                ip = result['ip_address']
                camera_id = result.get('camera_id', 'unknown')
                if actual_port not in discovered:
                    discovered[actual_port] = ip
                    found_ips.add(ip)
                    print(f"✓ 子機を検出: {ip}:{actual_port} (カメラID: {camera_id})")
                    # 見つかったカメラを即座に通知
                    if on_camera_found:
                        on_camera_found(actual_port, ip)
                    
                    # 同じIPアドレスの他のポートを優先的にスキャン
                    remaining_ports = [p for p in ports if p not in discovered]
                    if remaining_ports:
                        print(f"  → 同じIP ({ip}) の他のポートを優先スキャン: {remaining_ports}")
                        priority_tasks = [(ip, p) for p in remaining_ports]
                        # 優先スキャンを即座に実行
                        for priority_ip, priority_port in priority_tasks:
                            priority_result = scan_single_camera_info(priority_ip, priority_port, timeout, debug=False)
                            if priority_result:
                                priority_actual_port = priority_result['port']
                                priority_ip_addr = priority_result['ip_address']
                                priority_camera_id = priority_result.get('camera_id', 'unknown')
                                if priority_actual_port not in discovered:
                                    discovered[priority_actual_port] = priority_ip_addr
                                    found_ips.add(priority_ip_addr)
                                    print(f"✓ 子機を検出（優先スキャン）: {priority_ip_addr}:{priority_actual_port} (カメラID: {priority_camera_id})")
                                    # 見つかったカメラを即座に通知
                                    if on_camera_found:
                                        on_camera_found(priority_actual_port, priority_ip_addr)
                    
                    # 同じネットワーク範囲内の近接IPアドレスも優先的にスキャン（別の子機の可能性）
                    nearby_ips = get_nearby_ips(ip, range_size=20)  # 前後20個のIPアドレスをスキャン
                    if nearby_ips and len(discovered) < len(ports):
                        remaining_ports_for_nearby = [p for p in ports if p not in discovered]
                        if remaining_ports_for_nearby:
                            print(f"  → 近接IPアドレスを優先スキャン: {nearby_ips[:5]}... (合計{len(nearby_ips)}個) × ポート{remaining_ports_for_nearby}")
                            # 近接IPアドレスを優先的にスキャン（並列実行）
                            nearby_tasks = [(nearby_ip, p) for nearby_ip in nearby_ips for p in remaining_ports_for_nearby]
                            # 優先スキャンを並列実行（最大10並列）
                            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as nearby_executor:
                                nearby_futures = {
                                    nearby_executor.submit(scan_single_camera_info, nearby_ip, p, timeout, debug=False): (nearby_ip, p)
                                    for nearby_ip, p in nearby_tasks
                                }
                                for nearby_future in concurrent.futures.as_completed(nearby_futures):
                                    nearby_result = nearby_future.result()
                                    if nearby_result:
                                        nearby_actual_port = nearby_result['port']
                                        nearby_ip_addr = nearby_result['ip_address']
                                        nearby_camera_id = nearby_result.get('camera_id', 'unknown')
                                        if nearby_actual_port not in discovered:
                                            discovered[nearby_actual_port] = nearby_ip_addr
                                            found_ips.add(nearby_ip_addr)
                                            print(f"✓ 子機を検出（近接IP優先スキャン）: {nearby_ip_addr}:{nearby_actual_port} (カメラID: {nearby_camera_id})")
                                            # 見つかったカメラを即座に通知
                                            if on_camera_found:
                                                on_camera_found(nearby_actual_port, nearby_ip_addr)
                                            # 4台すべて見つかったら終了
                                            if len(discovered) >= len(ports):
                                                break
                                # 4台すべて見つかったら外側のループも終了
                                if len(discovered) >= len(ports):
                                    break
    
    elapsed_time = time.time() - start_time
    print(f"\n検出完了: {len(detected_cameras)}台の子機を検出しました (所要時間: {elapsed_time:.2f}秒)")
    
    # 親機のネットワーク範囲で見つからなかった場合、一般的なネットワーク範囲もスキャン
    if len(discovered) < len(ports):
        print(f"\n親機のネットワーク範囲で {len(discovered)}/{len(ports)} 台しか見つかりませんでした。")
        print("一般的なネットワーク範囲もスキャンします...")
        
        # 一般的なネットワーク範囲も含めてスキャン
        extended_network_range = get_all_network_ranges(include_common=True)
        # 既にスキャンしたIPアドレスを除外
        already_scanned = set(network_range)
        extended_ips = [ip for ip in extended_network_range if ip not in already_scanned]
        
        if extended_ips:
            print(f"追加スキャン対象: {len(extended_ips)}個のIPアドレス")
            
            # 追加のタスクを作成
            extended_tasks = []
            for ip in extended_ips:
                for port in ports:
                    if port not in discovered:  # 既に見つかったポートはスキップ
                        extended_tasks.append((ip, port))
            
            if extended_tasks:
                print(f"追加スキャン数: {len(extended_tasks)}")
                extended_start_time = time.time()
                
                # 並列処理で追加スキャン
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_task = {
                        executor.submit(scan_single_camera_info, ip, port, timeout): (ip, port)
                        for ip, port in extended_tasks
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_task):
                        result = future.result()
                        if result:
                            detected_cameras.append(result)
                            # /infoが返す実際のポート番号を使用
                            actual_port = result['port']  # 子機が実際に使用しているポート
                            ip = result['ip_address']
                            camera_id = result.get('camera_id', 'unknown')
                            if actual_port not in discovered:
                                discovered[actual_port] = ip
                                print(f"✓ 子機を検出（追加スキャン）: {ip}:{actual_port} (カメラID: {camera_id})")
                                # 見つかったカメラを即座に通知
                                if on_camera_found:
                                    on_camera_found(actual_port, ip)
                
                extended_elapsed_time = time.time() - extended_start_time
                print(f"追加スキャン完了: 合計 {len(detected_cameras)}台の子機を検出 (追加時間: {extended_elapsed_time:.2f}秒)")
    
    return discovered

if __name__ == '__main__':
    # テスト実行
    print("カメラ検出テスト（高速モード）...")
    cameras = discover_cameras_fast()
    
    print("\n検出結果:")
    for port, ip in cameras.items():
        print(f"  ポート {port}: {ip}")
    
    if not cameras:
        print("\nカメラが見つかりませんでした。")
        print("テストカメラサーバーを起動するには:")
        print("  python test_camera_server.py 0  # カメラ0 (ポート5000)")
        print("  python test_camera_server.py 1  # カメラ1 (ポート5001)")
        print("  python test_camera_server.py 2  # カメラ2 (ポート5002)")
        print("  python test_camera_server.py 3  # カメラ3 (ポート5003)")

