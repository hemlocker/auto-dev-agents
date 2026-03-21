#!/bin/bash

# 设备管理系统 - 健康检查脚本
# 用途：检查系统健康状态，支持 Cron 定时执行

set -e

# 颜色定义 (仅在终端输出时使用)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="${SCRIPT_DIR}/../deploy"
LOG_FILE="${SCRIPT_DIR}/health_check.log"
ALERT_EMAIL="${ALERT_EMAIL:-}"  # 可通过环境变量设置

# 检查计数
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# 日志函数
log() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_success() {
    log "${GREEN}✓ PASS${NC}" "$1"
    ((CHECKS_PASSED++))
}

log_warning() {
    log "${YELLOW}⚠ WARN${NC}" "$1"
    ((CHECKS_WARNING++))
}

log_error() {
    log "${RED}✗ FAIL${NC}" "$1"
    ((CHECKS_FAILED++))
}

# 检查 Docker 服务
check_docker_service() {
    local service_name=$1
    local container_name=$(docker-compose -p demo_project -f "${DEPLOY_DIR}/docker-compose.yml" ps -q ${service_name} 2>/dev/null)
    
    if [ -n "${container_name}" ]; then
        local status=$(docker inspect -f '{{.State.Status}}' "${container_name}" 2>/dev/null)
        if [ "${status}" = "running" ]; then
            log_success "Docker 服务 ${service_name} 运行正常"
            return 0
        else
            log_error "Docker 服务 ${service_name} 状态异常：${status}"
            return 1
        fi
    else
        log_error "Docker 服务 ${service_name} 容器不存在"
        return 1
    fi
}

# 检查 HTTP 端点
check_http_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local timeout=${3:-5}
    
    local status=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${timeout} "${url}" 2>/dev/null)
    
    if [ "${status}" = "${expected_status}" ]; then
        log_success "HTTP 端点 ${url} 响应正常 (状态码：${status})"
        return 0
    else
        log_error "HTTP 端点 ${url} 响应异常 (期望：${expected_status}, 实际：${status})"
        return 1
    fi
}

# 检查 API 健康
check_api_health() {
    local url=$1
    local timeout=${2:-5}
    
    local response=$(curl -s --max-time ${timeout} "${url}" 2>/dev/null)
    
    if [ -n "${response}" ]; then
        log_success "API 健康检查 ${url} 响应正常"
        return 0
    else
        log_error "API 健康检查 ${url} 无响应"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    local path=$1
    local threshold=${2:-80}
    
    local usage=$(df "${path}" 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ -n "${usage}" ] && [ "${usage}" -lt "${threshold}" ]; then
        log_success "磁盘空间充足 (${path}): ${usage}%"
        return 0
    elif [ -n "${usage}" ] && [ "${usage}" -lt 90 ]; then
        log_warning "磁盘空间警告 (${path}): ${usage}%"
        return 0
    else
        log_error "磁盘空间不足 (${path}): ${usage}%"
        return 1
    fi
}

# 检查内存使用
check_memory() {
    local threshold=${1:-80}
    
    local usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    if [ "${usage}" -lt "${threshold}" ]; then
        log_success "内存使用正常：${usage}%"
        return 0
    elif [ "${usage}" -lt 90 ]; then
        log_warning "内存使用警告：${usage}%"
        return 0
    else
        log_error "内存使用过高：${usage}%"
        return 1
    fi
}

# 检查 CPU 使用
check_cpu() {
    local threshold=${1:-80}
    
    # 获取 1 分钟平均负载
    local load=$(cat /proc/loadavg | awk '{print $1}')
    local cpu_count=$(nproc)
    local usage=$(echo "${load} ${cpu_count}" | awk '{printf("%.0f", ($1/$2)*100)}')
    
    if [ "${usage}" -lt "${threshold}" ]; then
        log_success "CPU 负载正常：${load} (${usage}%)"
        return 0
    elif [ "${usage}" -lt 90 ]; then
        log_warning "CPU 负载警告：${load} (${usage}%)"
        return 0
    else
        log_error "CPU 负载过高：${load} (${usage}%)"
        return 1
    fi
}

# 检查 Docker 容器日志
check_container_logs() {
    local service=$1
    local error_threshold=${2:-10}
    local time_range="5m"
    
    local error_count=$(docker-compose -p demo_project -f "${DEPLOY_DIR}/docker-compose.yml" logs --since="${time_range}" ${service} 2>/dev/null | grep -ci "error\|exception\|fatal" 2>/dev/null || echo "0")
    error_count=$(echo "${error_count}" | tr -d '[:space:]')
    
    # 确保 error_count 是数字
    if ! [[ "${error_count}" =~ ^[0-9]+$ ]]; then
        error_count=0
    fi
    
    if [ "${error_count}" -lt "${error_threshold}" ]; then
        log_success "容器 ${service} 日志正常 (错误数：${error_count})"
        return 0
    else
        log_error "容器 ${service} 错误日志过多 (${error_count} > ${error_threshold})"
        return 1
    fi
}

# 检查数据库文件
check_database() {
    local db_path="${DEPLOY_DIR}/../data"
    
    # 检查数据库目录是否存在
    if [ -d "${db_path}" ]; then
        local db_size=$(du -sh "${db_path}" 2>/dev/null | cut -f1)
        log_success "数据库目录存在，大小：${db_size}"
        return 0
    else
        log_warning "数据库目录不存在：${db_path}"
        return 0
    fi
}

# 检查网络连接
check_network() {
    local host=$1
    local port=$2
    local timeout=${3:-3}
    
    if timeout ${timeout} bash -c "cat < /dev/null > /dev/tcp/${host}/${port}" 2>/dev/null; then
        log_success "网络连接正常：${host}:${port}"
        return 0
    else
        log_error "网络连接失败：${host}:${port}"
        return 1
    fi
}

# 发送告警
send_alert() {
    local subject=$1
    local message=$2
    
    if [ -n "${ALERT_EMAIL}" ]; then
        echo "${message}" | mail -s "${subject}" "${ALERT_EMAIL}" 2>/dev/null || true
        log "告警邮件已发送至：${ALERT_EMAIL}"
    fi
    
    # 可以添加其他告警方式：钉钉、企业微信、Slack 等
}

# 生成报告
generate_report() {
    local report_file="${SCRIPT_DIR}/health_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "${report_file}" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "summary": {
        "passed": ${CHECKS_PASSED},
        "failed": ${CHECKS_FAILED},
        "warning": ${CHECKS_WARNING},
        "total": $((CHECKS_PASSED + CHECKS_FAILED + CHECKS_WARNING))
    },
    "status": "$([ ${CHECKS_FAILED} -eq 0 ] && echo 'healthy' || echo 'unhealthy')"
}
EOF
    
    log "健康检查报告已生成：${report_file}"
    echo "${report_file}"
}

# 主函数
main() {
    log "=========================================="
    log "开始健康检查"
    log "=========================================="
    
    # 进入部署目录
    cd "${DEPLOY_DIR}" || exit 1
    
    # 1. Docker 服务检查
    log "--- Docker 服务检查 ---"
    check_docker_service "frontend" || true
    check_docker_service "backend" || true
    
    # 2. HTTP 端点检查
    log "--- HTTP 端点检查 ---"
    check_http_endpoint "http://localhost" 200 5 || true
    check_http_endpoint "http://localhost/api" 200 5 || true
    
    # 3. 系统资源检查
    log "--- 系统资源检查 ---"
    check_disk_space "/" 80 || true
    check_memory 80 || true
    check_cpu 80 || true
    
    # 4. 容器日志检查
    log "--- 容器日志检查 ---"
    check_container_logs "backend" 10 || true
    check_container_logs "frontend" 10 || true
    
    # 5. 数据库检查
    log "--- 数据库检查 ---"
    check_database || true
    
    # 6. 网络检查
    log "--- 网络连接检查 ---"
    check_network "localhost" "80" 3 || true
    check_network "localhost" "3000" 3 || true
    
    # 生成报告
    log "=========================================="
    log "健康检查完成"
    log "通过：${CHECKS_PASSED}, 失败：${CHECKS_FAILED}, 警告：${CHECKS_WARNING}"
    log "=========================================="
    
    local report_file=$(generate_report)
    
    # 如果有失败的检查，发送告警
    if [ ${CHECKS_FAILED} -gt 0 ]; then
        send_alert "[告警] 设备管理系统健康检查失败" "检查失败数：${CHECKS_FAILED}\n报告文件：${report_file}"
        exit 1
    elif [ ${CHECKS_WARNING} -gt 0 ]; then
        send_alert "[警告] 设备管理系统健康检查警告" "检查警告数：${CHECKS_WARNING}\n报告文件：${report_file}"
        exit 0
    else
        exit 0
    fi
}

# 执行主函数
main "$@"
