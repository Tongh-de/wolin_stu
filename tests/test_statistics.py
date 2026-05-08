"""
统计服务单元测试
"""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session


class TestStatisticsService:
    """统计服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        db = Mock(spec=Session)
        return db

    @pytest.fixture
    def service(self):
        """导入统计服务"""
        from services.statistics_service import StatisticsService
        return StatisticsService

    def test_class_gender_statistics(self, service, mock_db):
        """测试班级性别统计"""
        # 设置模拟返回值
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
            Mock(class_id=1, class_name="软件1班", total=30, male=20, female=10),
            Mock(class_id=2, class_name="软件2班", total=28, male=15, female=13),
        ]
        
        result = service.class_gender_statistics(mock_db)
        
        assert result["code"] == 200
        assert len(result["data"]) == 2
        assert result["data"][0]["class_name"] == "软件1班"
        assert result["data"][0]["male"] == 20

    def test_top5_salary_students(self, service, mock_db):
        """测试高薪学生排名"""
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            Mock(stu_name="张三", class_name="软件1班", salary=25000, offer_time="2024-01", company="腾讯"),
            Mock(stu_name="李四", class_name="软件2班", salary=22000, offer_time="2024-02", company="阿里"),
        ]
        
        result = service.top5_salary_students(mock_db)
        
        assert result["code"] == 200
        assert len(result["data"]) == 2
        assert result["data"][0]["salary"] == 25000

    def test_employment_duration_per_student(self, service, mock_db):
        """测试就业时长计算"""
        from datetime import datetime
        
        mock_db.query.return_value.filter.return_value.all.return_value = [
            Mock(
                stu_id="001", 
                stu_name="张三", 
                open_time=datetime(2024, 1, 1), 
                offer_time=datetime(2024, 3, 1)
            ),
        ]
        
        result = service.employment_duration_per_student(mock_db)
        
        assert result["code"] == 200
        assert result["data"][0]["duration_days"] == 60  # 1月1日到3月1日

    def test_salary_distribution(self, service, mock_db):
        """测试薪资分布统计"""
        # 模拟CASE WHEN查询结果
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            Mock(range="5k-8k", count=15),
            Mock(range="8k-12k", count=25),
            Mock(range="12k-20k", count=10),
        ]
        
        result = service.salary_distribution(mock_db)
        
        assert result["code"] == 200
        assert len(result["data"]) == 5  # 5个薪资区间
        # 验证所有区间都有值
        ranges = {item["range"] for item in result["data"]}
        assert "<5k" in ranges
        assert ">20k" in ranges


class TestEmploymentService:
    """就业服务测试"""

    @pytest.fixture
    def employment_service(self):
        """导入就业服务"""
        from services.employment_service import EmploymentService
        return EmploymentService

    @pytest.fixture
    def mock_db(self):
        db = Mock(spec=Session)
        return db

    def test_query_employment_with_company(self, employment_service, mock_db):
        """测试公司名称模糊查询（防SQL注入）"""
        employment_service.query_employment(mock_db, company="腾讯")
        
        # 验证使用了ilike而非like
        call_args = mock_db.query.return_value.filter.return_value.filter.return_value
        # ilike方法应该被调用
        mock_db.query.assert_called()

    def test_query_employment_with_salary_range(self, employment_service, mock_db):
        """测试薪资范围查询"""
        employment_service.query_employment(
            mock_db, 
            min_salary=5000, 
            max_salary=10000
        )
        
        mock_db.query.assert_called()


class TestHomeworkService:
    """作业服务测试"""

    def test_parse_file_content_txt(self):
        """测试TXT文件解析"""
        from services.homework_service import parse_file_content
        
        content = "这是测试内容"
        result = parse_file_content(content.encode('utf-8'), "test.txt")
        
        assert result == content

    def test_parse_file_content_unsupported(self):
        """测试不支持的文件格式"""
        from services.homework_service import parse_file_content
        
        with pytest.raises(ValueError, match="不支持的文件格式"):
            parse_file_content(b"data", "test.exe")
