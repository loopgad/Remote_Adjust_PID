/**
 * @file matrix.cpp
 * @brief 数学核心层实现
 */

#include "../../include/math/matrix.h"
#include <cmath>
#include <algorithm>
#include <numeric>
#include <stdexcept>
#include <cstring>

namespace param_id {
namespace math {

// ============================================================================
// Vector实现
// ============================================================================

Vector Vector::operator+(const Vector& other) const {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = data_[i] + other[i];
    return result;
}

Vector Vector::operator-(const Vector& other) const {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = data_[i] - other[i];
    return result;
}

Vector Vector::operator*(double scalar) const {
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = data_[i] * scalar;
    return result;
}

Vector Vector::operator/(double scalar) const {
    if (scalar == 0.0) throw std::invalid_argument("Division by zero");
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = data_[i] / scalar;
    return result;
}

Vector& Vector::operator+=(const Vector& other) {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    for (size_t i = 0; i < size(); ++i) data_[i] += other[i];
    return *this;
}

Vector& Vector::operator-=(const Vector& other) {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    for (size_t i = 0; i < size(); ++i) data_[i] -= other[i];
    return *this;
}

Vector& Vector::operator*=(double scalar) {
    for (auto& v : data_) v *= scalar;
    return *this;
}

Vector& Vector::operator/=(double scalar) {
    if (scalar == 0.0) throw std::invalid_argument("Division by zero");
    for (auto& v : data_) v /= scalar;
    return *this;
}

double Vector::dot(const Vector& other) const {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    double sum = 0.0;
    for (size_t i = 0; i < size(); ++i) sum += data_[i] * other[i];
    return sum;
}

double Vector::norm() const {
    return std::sqrt(norm_sq());
}

double Vector::norm_sq() const {
    return dot(*this);
}

Vector Vector::normalized() const {
    double n = norm();
    if (n < 1e-15) return Vector(size(), 0.0);
    return *this / n;
}

Vector Vector::cwise_mul(const Vector& other) const {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = data_[i] * other[i];
    return result;
}

Vector Vector::cwise_div(const Vector& other) const {
    if (size() != other.size()) throw std::invalid_argument("Vector size mismatch");
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) {
        if (other[i] == 0.0) throw std::invalid_argument("Division by zero");
        result[i] = data_[i] / other[i];
    }
    return result;
}

Vector Vector::cwise_abs() const {
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = std::abs(data_[i]);
    return result;
}

Vector Vector::cwise_max(double val) const {
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = std::max(data_[i], val);
    return result;
}

Vector Vector::cwise_min(double val) const {
    Vector result(size());
    for (size_t i = 0; i < size(); ++i) result[i] = std::min(data_[i], val);
    return result;
}

double Vector::sum() const {
    return std::accumulate(data_.begin(), data_.end(), 0.0);
}

double Vector::mean() const {
    if (empty()) throw std::invalid_argument("Empty vector");
    return sum() / size();
}

double Vector::max() const {
    if (empty()) throw std::invalid_argument("Empty vector");
    return *std::max_element(data_.begin(), data_.end());
}

double Vector::min() const {
    if (empty()) throw std::invalid_argument("Empty vector");
    return *std::min_element(data_.begin(), data_.end());
}

size_t Vector::argmax() const {
    if (empty()) throw std::invalid_argument("Empty vector");
    return std::distance(data_.begin(), std::max_element(data_.begin(), data_.end()));
}

size_t Vector::argmin() const {
    if (empty()) throw std::invalid_argument("Empty vector");
    return std::distance(data_.begin(), std::min_element(data_.begin(), data_.end()));
}

Vector Vector::zeros(size_t n) { return Vector(n, 0.0); }
Vector Vector::ones(size_t n) { return Vector(n, 1.0); }

Vector Vector::linspace(double start, double end, size_t n) {
    if (n == 0) return Vector();
    if (n == 1) return Vector{start};
    Vector result(n);
    double step = (end - start) / (n - 1);
    for (size_t i = 0; i < n; ++i) result[i] = start + i * step;
    return result;
}

Vector Vector::range(size_t n) {
    Vector result(n);
    for (size_t i = 0; i < n; ++i) result[i] = static_cast<double>(i);
    return result;
}

Vector operator*(double scalar, const Vector& v) { return v * scalar; }

// ============================================================================
// Matrix实现
// ============================================================================

Matrix::Matrix(size_t rows, size_t cols, double val)
    : rows_(rows), cols_(cols), data_(rows * cols, val) {}

Matrix::Matrix(size_t rows, size_t cols, const std::vector<double>& data)
    : rows_(rows), cols_(cols), data_(data) {
    if (data.size() != rows * cols) throw std::invalid_argument("Data size mismatch");
}

Matrix::Matrix(std::initializer_list<std::initializer_list<double>> init) {
    rows_ = init.size();
    if (rows_ == 0) { cols_ = 0; return; }
    cols_ = init.begin()->size();
    data_.reserve(rows_ * cols_);
    for (const auto& row : init) {
        if (row.size() != cols_) throw std::invalid_argument("Row size mismatch");
        data_.insert(data_.end(), row.begin(), row.end());
    }
}

Vector Matrix::row(size_t i) const {
    Vector result(cols_);
    for (size_t j = 0; j < cols_; ++j) result[j] = (*this)(i, j);
    return result;
}

Vector Matrix::col(size_t j) const {
    Vector result(rows_);
    for (size_t i = 0; i < rows_; ++i) result[i] = (*this)(i, j);
    return result;
}

void Matrix::set_row(size_t i, const Vector& v) {
    if (v.size() != cols_) throw std::invalid_argument("Vector size mismatch");
    for (size_t j = 0; j < cols_; ++j) (*this)(i, j) = v[j];
}

void Matrix::set_col(size_t j, const Vector& v) {
    if (v.size() != rows_) throw std::invalid_argument("Vector size mismatch");
    for (size_t i = 0; i < rows_; ++i) (*this)(i, j) = v[i];
}

Matrix Matrix::operator+(const Matrix& other) const {
    if (rows_ != other.rows_ || cols_ != other.cols_) throw std::invalid_argument("Matrix size mismatch");
    Matrix result(rows_, cols_);
    for (size_t i = 0; i < size(); ++i) result.data_[i] = data_[i] + other.data_[i];
    return result;
}

Matrix Matrix::operator-(const Matrix& other) const {
    if (rows_ != other.rows_ || cols_ != other.cols_) throw std::invalid_argument("Matrix size mismatch");
    Matrix result(rows_, cols_);
    for (size_t i = 0; i < size(); ++i) result.data_[i] = data_[i] - other.data_[i];
    return result;
}

Matrix Matrix::operator*(double scalar) const {
    Matrix result(rows_, cols_);
    for (size_t i = 0; i < size(); ++i) result.data_[i] = data_[i] * scalar;
    return result;
}

Matrix Matrix::operator/(double scalar) const {
    if (scalar == 0.0) throw std::invalid_argument("Division by zero");
    Matrix result(rows_, cols_);
    for (size_t i = 0; i < size(); ++i) result.data_[i] = data_[i] / scalar;
    return result;
}

Matrix& Matrix::operator+=(const Matrix& other) {
    if (rows_ != other.rows_ || cols_ != other.cols_) throw std::invalid_argument("Matrix size mismatch");
    for (size_t i = 0; i < size(); ++i) data_[i] += other.data_[i];
    return *this;
}

Matrix& Matrix::operator-=(const Matrix& other) {
    if (rows_ != other.rows_ || cols_ != other.cols_) throw std::invalid_argument("Matrix size mismatch");
    for (size_t i = 0; i < size(); ++i) data_[i] -= other.data_[i];
    return *this;
}

Matrix& Matrix::operator*=(double scalar) {
    for (auto& v : data_) v *= scalar;
    return *this;
}

Matrix Matrix::operator*(const Matrix& other) const {
    if (cols_ != other.rows_) throw std::invalid_argument("Matrix size mismatch for multiplication");
    Matrix result(rows_, other.cols_, 0.0);
    for (size_t i = 0; i < rows_; ++i) {
        for (size_t k = 0; k < cols_; ++k) {
            double aik = (*this)(i, k);
            for (size_t j = 0; j < other.cols_; ++j) {
                result(i, j) += aik * other(k, j);
            }
        }
    }
    return result;
}

Vector Matrix::operator*(const Vector& v) const {
    if (cols_ != v.size()) throw std::invalid_argument("Matrix-Vector size mismatch");
    Vector result(rows_, 0.0);
    for (size_t i = 0; i < rows_; ++i) {
        for (size_t j = 0; j < cols_; ++j) {
            result[i] += (*this)(i, j) * v[j];
        }
    }
    return result;
}

Matrix Matrix::transpose() const {
    Matrix result(cols_, rows_);
    for (size_t i = 0; i < rows_; ++i) {
        for (size_t j = 0; j < cols_; ++j) {
            result(j, i) = (*this)(i, j);
        }
    }
    return result;
}

Matrix Matrix::identity(size_t n) {
    Matrix m(n, n, 0.0);
    for (size_t i = 0; i < n; ++i) m(i, i) = 1.0;
    return m;
}

Matrix Matrix::zeros(size_t rows, size_t cols) { return Matrix(rows, cols, 0.0); }

Matrix Matrix::diag(const Vector& v) {
    size_t n = v.size();
    Matrix m(n, n, 0.0);
    for (size_t i = 0; i < n; ++i) m(i, i) = v[i];
    return m;
}

double Matrix::determinant() const {
    if (rows_ != cols_) throw std::invalid_argument("Determinant requires square matrix");
    size_t n = rows_;
    if (n == 1) return data_[0];
    if (n == 2) return data_[0] * data_[3] - data_[1] * data_[2];
    if (n == 3) {
        return data_[0] * (data_[4] * data_[8] - data_[5] * data_[7])
             - data_[1] * (data_[3] * data_[8] - data_[5] * data_[6])
             + data_[2] * (data_[3] * data_[7] - data_[4] * data_[6]);
    }
    // LU分解计算行列式
    Matrix L(n, n, 0.0), U(n, n, 0.0);
    std::vector<int> perm(n);
    lu_decompose(L, U, perm);
    double det = 1.0;
    int sign = 1;
    for (size_t i = 0; i < n; ++i) {
        det *= U(i, i);
        if (perm[i] != static_cast<int>(i)) sign *= -1;
    }
    return det * sign;
}

Matrix Matrix::inverse() const {
    if (rows_ != cols_) throw std::invalid_argument("Inverse requires square matrix");
    size_t n = rows_;
    if (n == 1) {
        if (data_[0] == 0.0) throw std::runtime_error("Singular matrix");
        return Matrix(1, 1, {1.0 / data_[0]});
    }
    if (n == 2) {
        double det = data_[0] * data_[3] - data_[1] * data_[2];
        if (std::abs(det) < 1e-15) throw std::runtime_error("Singular matrix");
        return Matrix(2, 2, {data_[3] / det, -data_[1] / det, -data_[2] / det, data_[0] / det});
    }
    // Gauss-Jordan消元
    Matrix augmented(n, 2 * n, 0.0);
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) augmented(i, j) = (*this)(i, j);
        augmented(i, n + i) = 1.0;
    }
    for (size_t i = 0; i < n; ++i) {
        size_t max_row = i;
        for (size_t k = i + 1; k < n; ++k) {
            if (std::abs(augmented(k, i)) > std::abs(augmented(max_row, i))) max_row = k;
        }
        if (max_row != i) {
            for (size_t j = 0; j < 2 * n; ++j) std::swap(augmented(i, j), augmented(max_row, j));
        }
        if (std::abs(augmented(i, i)) < 1e-15) throw std::runtime_error("Singular matrix");
        double pivot = augmented(i, i);
        for (size_t j = 0; j < 2 * n; ++j) augmented(i, j) /= pivot;
        for (size_t k = 0; k < n; ++k) {
            if (k == i) continue;
            double factor = augmented(k, i);
            for (size_t j = 0; j < 2 * n; ++j) augmented(k, j) -= factor * augmented(i, j);
        }
    }
    Matrix result(n, n);
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) result(i, j) = augmented(i, n + j);
    }
    return result;
}

void Matrix::lu_decompose(Matrix& L, Matrix& U, std::vector<int>& perm) const {
    size_t n = rows_;
    U = *this;
    L = Matrix::identity(n);
    for (size_t i = 0; i < n; ++i) perm[i] = static_cast<int>(i);
    for (size_t i = 0; i < n; ++i) {
        size_t max_row = i;
        for (size_t k = i + 1; k < n; ++k) {
            if (std::abs(U(k, i)) > std::abs(U(max_row, i))) max_row = k;
        }
        if (max_row != i) {
            for (size_t j = 0; j < n; ++j) std::swap(U(i, j), U(max_row, j));
            for (size_t j = 0; j < i; ++j) std::swap(L(i, j), L(max_row, j));
            std::swap(perm[i], perm[max_row]);
        }
        for (size_t k = i + 1; k < n; ++k) {
            L(k, i) = U(k, i) / U(i, i);
            for (size_t j = i; j < n; ++j) U(k, j) -= L(k, i) * U(i, j);
        }
    }
}

Matrix operator*(double scalar, const Matrix& m) { return m * scalar; }

// ============================================================================
// 数值积分实现
// ============================================================================

namespace integration {

// Forward declaration
static double adaptive_simpson_helper(double (*f)(double), double a, double b, double tol,
                                       double S, double fa, double fb, double fc);

double trapz(const Vector& x, const Vector& y) {
    if (x.size() != y.size()) throw std::invalid_argument("Vector size mismatch");
    if (x.size() < 2) return 0.0;
    double sum = 0.0;
    for (size_t i = 1; i < x.size(); ++i) {
        sum += 0.5 * (y[i] + y[i-1]) * (x[i] - x[i-1]);
    }
    return sum;
}

double simpson(double (*f)(double), double a, double b, int n) {
    if (n % 2 != 0) n++;
    double h = (b - a) / n;
    double sum = f(a) + f(b);
    for (int i = 1; i < n; i += 2) sum += 4.0 * f(a + i * h);
    for (int i = 2; i < n; i += 2) sum += 2.0 * f(a + i * h);
    return sum * h / 3.0;
}

double adaptive_simpson(double (*f)(double), double a, double b, double tol) {
    double c = (a + b) / 2.0;
    double fa = f(a), fb = f(b), fc = f(c);
    double S = (b - a) / 6.0 * (fa + 4.0 * fc + fb);
    return adaptive_simpson_helper(f, a, b, tol, S, fa, fb, fc);
}

static double adaptive_simpson_helper(double (*f)(double), double a, double b, double tol,
                                       double S, double fa, double fb, double fc) {
    double c = (a + b) / 2.0;
    double h = b - a;
    double d = (a + c) / 2.0, e = (c + b) / 2.0;
    double fd = f(d), fe = f(e);
    double S1 = h / 12.0 * (fa + 4.0 * fd + fc);
    double S2 = h / 12.0 * (fc + 4.0 * fe + fb);
    double error = (S1 + S2 - S) / 15.0;
    if (std::abs(error) < tol) return S1 + S2 + error;
    return adaptive_simpson_helper(f, a, c, tol / 2.0, S1, fa, fc, fd)
         + adaptive_simpson_helper(f, c, b, tol / 2.0, S2, fc, fb, fe);
}

} // namespace integration

// ============================================================================
// 线性代数实现
// ============================================================================

namespace linalg {

Vector solve(const Matrix& A, const Vector& b) {
    size_t n = A.rows();
    if (A.cols() != n || b.size() != n) throw std::invalid_argument("Size mismatch");
    // Gauss消元
    Matrix aug(n, n + 1);
    for (size_t i = 0; i < n; ++i) {
        for (size_t j = 0; j < n; ++j) aug(i, j) = A(i, j);
        aug(i, n) = b[i];
    }
    for (size_t i = 0; i < n; ++i) {
        size_t max_row = i;
        for (size_t k = i + 1; k < n; ++k) {
            if (std::abs(aug(k, i)) > std::abs(aug(max_row, i))) max_row = k;
        }
        if (max_row != i) {
            for (size_t j = 0; j <= n; ++j) std::swap(aug(i, j), aug(max_row, j));
        }
        if (std::abs(aug(i, i)) < 1e-15) throw std::runtime_error("Singular matrix");
        double pivot = aug(i, i);
        for (size_t j = i; j <= n; ++j) aug(i, j) /= pivot;
        for (size_t k = 0; k < n; ++k) {
            if (k == i) continue;
            double factor = aug(k, i);
            for (size_t j = i; j <= n; ++j) aug(k, j) -= factor * aug(i, j);
        }
    }
    Vector x(n);
    for (size_t i = 0; i < n; ++i) x[i] = aug(i, n);
    return x;
}

Vector lstsq(const Matrix& A, const Vector& b) {
    // A^T A x = A^T b
    Matrix At = A.transpose();
    Matrix AtA = At * A;
    Vector Atb = At * b;
    return solve(AtA, Atb);
}

void eigen_symmetric(const Matrix& A, Vector& eigenvalues, Matrix& eigenvectors) {
    // 简化的Jacobi方法，适用于小矩阵
    size_t n = A.rows();
    eigenvectors = Matrix::identity(n);
    eigenvalues = Vector(n);
    Matrix B = A;
    for (int iter = 0; iter < 100; ++iter) {
        double max_off = 0.0;
        size_t p = 0, q = 1;
        for (size_t i = 0; i < n; ++i) {
            for (size_t j = i + 1; j < n; ++j) {
                if (std::abs(B(i, j)) > max_off) {
                    max_off = std::abs(B(i, j));
                    p = i; q = j;
                }
            }
        }
        if (max_off < 1e-10) break;
        double theta = 0.5 * std::atan2(2.0 * B(p, q), B(p, p) - B(q, q));
        double c = std::cos(theta), s = std::sin(theta);
        Matrix R = Matrix::identity(n);
        R(p, p) = c; R(q, q) = c;
        R(p, q) = -s; R(q, p) = s;
        B = R.transpose() * B * R;
        eigenvectors = eigenvectors * R;
    }
    for (size_t i = 0; i < n; ++i) eigenvalues[i] = B(i, i);
}

void svd(const Matrix& A, Matrix& U, Vector& S, Matrix& V) {
    // 简化实现：使用 A^T A 的特征值分解
    Matrix AtA = A.transpose() * A;
    Vector eigenvalues;
    eigen_symmetric(AtA, eigenvalues, V);
    size_t n = std::min(A.rows(), A.cols());
    S = Vector(n);
    for (size_t i = 0; i < n; ++i) S[i] = std::sqrt(std::max(0.0, eigenvalues[i]));
    // 排序
    std::vector<size_t> indices(n);
    std::iota(indices.begin(), indices.end(), 0);
    std::sort(indices.begin(), indices.end(), [&](size_t a, size_t b) { return S[a] > S[b]; });
    Vector sorted_S(n);
    Matrix sorted_V(V.rows(), n);
    for (size_t i = 0; i < n; ++i) {
        sorted_S[i] = S[indices[i]];
        for (size_t j = 0; j < V.rows(); ++j) sorted_V(j, i) = V(j, indices[i]);
    }
    S = sorted_S;
    V = sorted_V;
    // U = A * V * S^{-1}
    U = Matrix(A.rows(), n);
    for (size_t i = 0; i < n; ++i) {
        if (S[i] > 1e-10) {
            Vector col = A * V.col(i) / S[i];
            U.set_col(i, col);
        }
    }
}

} // namespace linalg

} // namespace math
} // namespace param_id
