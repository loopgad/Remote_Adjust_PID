#pragma once
/**
 * @file matrix.h
 * @brief 数学核心层 - 矩阵与向量运算
 *
 * 提供高性能的矩阵/向量运算，基于Eigen库。
 * 用于物理模型仿真、优化算法、信号处理等。
 *
 * @author param_id_gui
 * @version 2.0
 */

#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <initializer_list>

namespace param_id {
namespace math {

// ============================================================================
// 向量类 - 轻量级动态向量
// ============================================================================

class Vector {
public:
    Vector() = default;
    explicit Vector(size_t n, double val = 0.0) : data_(n, val) {}
    Vector(std::initializer_list<double> init) : data_(init) {}
    Vector(const std::vector<double>& v) : data_(v) {}
    Vector(std::vector<double>&& v) : data_(std::move(v)) {}

    // 访问
    double& operator[](size_t i) { return data_[i]; }
    const double& operator[](size_t i) const { return data_[i]; }
    double& at(size_t i) { return data_.at(i); }
    const double& at(size_t i) const { return data_.at(i); }
    size_t size() const { return data_.size(); }
    bool empty() const { return data_.empty(); }
    void resize(size_t n, double val = 0.0) { data_.resize(n, val); }
    void clear() { data_.clear(); }
    double* data() { return data_.data(); }
    const double* data() const { return data_.data(); }

    // 迭代器
    auto begin() { return data_.begin(); }
    auto end() { return data_.end(); }
    auto begin() const { return data_.begin(); }
    auto end() const { return data_.end(); }

    // 算术运算
    Vector operator+(const Vector& other) const;
    Vector operator-(const Vector& other) const;
    Vector operator*(double scalar) const;
    Vector operator/(double scalar) const;
    Vector& operator+=(const Vector& other);
    Vector& operator-=(const Vector& other);
    Vector& operator*=(double scalar);
    Vector& operator/=(double scalar);

    // 点积
    double dot(const Vector& other) const;

    // 范数
    double norm() const;
    double norm_sq() const;
    Vector normalized() const;

    // 逐元素运算
    Vector cwise_mul(const Vector& other) const;
    Vector cwise_div(const Vector& other) const;
    Vector cwise_abs() const;
    Vector cwise_max(double val) const;
    Vector cwise_min(double val) const;

    // 聚合
    double sum() const;
    double mean() const;
    double max() const;
    double min() const;
    size_t argmax() const;
    size_t argmin() const;

    // 工厂方法
    static Vector zeros(size_t n);
    static Vector ones(size_t n);
    static Vector linspace(double start, double end, size_t n);
    static Vector range(size_t n);

    // 转换
    std::vector<double>& to_std() { return data_; }
    const std::vector<double>& to_std() const { return data_; }

private:
    std::vector<double> data_;
};

// 标量 * 向量
Vector operator*(double scalar, const Vector& v);

// ============================================================================
// 矩阵类 - 行主序动态矩阵
// ============================================================================

class Matrix {
public:
    Matrix() = default;
    Matrix(size_t rows, size_t cols, double val = 0.0);
    Matrix(size_t rows, size_t cols, const std::vector<double>& data);
    Matrix(std::initializer_list<std::initializer_list<double>> init);

    // 访问
    double& operator()(size_t i, size_t j) { return data_[i * cols_ + j]; }
    const double& operator()(size_t i, size_t j) const { return data_[i * cols_ + j]; }
    size_t rows() const { return rows_; }
    size_t cols() const { return cols_; }
    size_t size() const { return rows_ * cols_; }

    // 行/列访问
    Vector row(size_t i) const;
    Vector col(size_t j) const;
    void set_row(size_t i, const Vector& v);
    void set_col(size_t j, const Vector& v);

    // 算术运算
    Matrix operator+(const Matrix& other) const;
    Matrix operator-(const Matrix& other) const;
    Matrix operator*(double scalar) const;
    Matrix operator/(double scalar) const;
    Matrix& operator+=(const Matrix& other);
    Matrix& operator-=(const Matrix& other);
    Matrix& operator*=(double scalar);

    // 矩阵乘法
    Matrix operator*(const Matrix& other) const;
    Vector operator*(const Vector& v) const;

    // 转置
    Matrix transpose() const;

    // 行列式 (仅限小矩阵)
    double determinant() const;

    // 逆矩阵 (仅限小矩阵)
    Matrix inverse() const;

    // 工厂方法
    static Matrix identity(size_t n);
    static Matrix zeros(size_t rows, size_t cols);
    static Matrix diag(const Vector& v);

    // 数据访问
    double* data() { return data_.data(); }
    const double* data() const { return data_.data(); }

private:
    size_t rows_ = 0;
    size_t cols_ = 0;
    std::vector<double> data_;

    // LU分解辅助
    void lu_decompose(Matrix& L, Matrix& U, std::vector<int>& perm) const;
};

// 标量 * 矩阵
Matrix operator*(double scalar, const Matrix& m);

// ============================================================================
// 数值积分
// ============================================================================

namespace integration {

/**
 * @brief 梯形法则数值积分
 * @param x 自变量数组
 * @param y 因变量数组
 * @return 积分值
 */
double trapz(const Vector& x, const Vector& y);

/**
 * @brief 辛普森法则数值积分
 * @param f 被积函数
 * @param a 下限
 * @param b 上限
 * @param n 区间数 (必须为偶数)
 * @return 积分值
 */
double simpson(double (*f)(double), double a, double b, int n = 100);

/**
 * @brief 自适应辛普森积分
 * @param f 被积函数
 * @param a 下限
 * @param b 上限
 * @param tol 容差
 * @return 积分值
 */
double adaptive_simpson(double (*f)(double), double a, double b, double tol = 1e-8);

} // namespace integration

// ============================================================================
// 线性代数
// ============================================================================

namespace linalg {

/**
 * @brief 求解线性方程组 Ax = b
 * @param A 系数矩阵
 * @param b 右端向量
 * @return 解向量
 */
Vector solve(const Matrix& A, const Vector& b);

/**
 * @brief 最小二乘求解 min ||Ax - b||^2
 * @param A 系数矩阵
 * @param b 右端向量
 * @return 解向量
 */
Vector lstsq(const Matrix& A, const Vector& b);

/**
 * @brief 特征值分解 (仅限对称矩阵)
 * @param A 对称矩阵
 * @param eigenvalues 输出特征值
 * @param eigenvectors 输出特征向量
 */
void eigen_symmetric(const Matrix& A, Vector& eigenvalues, Matrix& eigenvectors);

/**
 * @brief SVD分解
 * @param A 输入矩阵
 * @param U 左奇异向量
 * @param S 奇异值
 * @param V 右奇异向量
 */
void svd(const Matrix& A, Matrix& U, Vector& S, Matrix& V);

} // namespace linalg

} // namespace math
} // namespace param_id
