# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 05 · Сортировки (10 алгоритмов)
"""

import random


def bubble_sort(arr):
    a = arr[:]
    n = len(a)
    for i in range(n):
        for j in range(n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
    return a


def selection_sort(arr):
    a = arr[:]
    for i in range(len(a)):
        mn = i
        for j in range(i + 1, len(a)):
            if a[j] < a[mn]:
                mn = j
        a[i], a[mn] = a[mn], a[i]
    return a


def insertion_sort(arr):
    a = arr[:]
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left, right = merge_sort(arr[:mid]), merge_sort(arr[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1
    return out + left[i:] + right[j:]


def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    less = [x for x in arr if x < pivot]
    eq = [x for x in arr if x == pivot]
    more = [x for x in arr if x > pivot]
    return quick_sort(less) + eq + quick_sort(more)


def heap_sort(arr):
    a = arr[:]
    n = len(a)

    def heapify(i, size):
        largest = i
        l, r = 2 * i + 1, 2 * i + 2
        if l < size and a[l] > a[largest]:
            largest = l
        if r < size and a[r] > a[largest]:
            largest = r
        if largest != i:
            a[i], a[largest] = a[largest], a[i]
            heapify(largest, size)

    for i in range(n // 2 - 1, -1, -1):
        heapify(i, n)
    for i in range(n - 1, 0, -1):
        a[0], a[i] = a[i], a[0]
        heapify(0, i)
    return a


def counting_sort(arr, max_val=1000):
    counts = [0] * (max_val + 1)
    for x in arr:
        counts[x] += 1
    out = []
    for v, c in enumerate(counts):
        out.extend([v] * c)
    return out


def bucket_sort(arr, n_buckets=10):
    if not arr:
        return arr
    mn, mx = min(arr), max(arr)
    rng = (mx - mn) / n_buckets or 1
    buckets = [[] for _ in range(n_buckets)]
    for x in arr:
        idx = min(int((x - mn) / rng), n_buckets - 1)
        buckets[idx].append(x)
    out = []
    for b in buckets:
        out.extend(sorted(b))
    return out


def radix_sort(arr):
    if not arr:
        return arr
    a = arr[:]
    mx = max(a)
    exp = 1
    while mx // exp > 0:
        out = [0] * len(a)
        counts = [0] * 10
        for x in a:
            counts[(x // exp) % 10] += 1
        for i in range(1, 10):
            counts[i] += counts[i - 1]
        for x in reversed(a):
            idx = (x // exp) % 10
            counts[idx] -= 1
            out[counts[idx]] = x
        a = out
        exp *= 10
    return a


def timsort(arr):
    """Timsort: использующий встроенную сортировку Python + слияние (реализация-мини)."""
    import bisect
    a = arr[:]
    runs = 32
    for i in range(0, len(a), runs):
        a[i:i + runs] = sorted(a[i:i + runs])
    size = runs
    while size < len(a):
        step = size * 2
        for start in range(0, len(a), step):
            mid = min(start + size, len(a))
            end = min(start + step, len(a))
            a[start:end] = merge_sort(a[start:mid]) + merge_sort(a[mid:end])
            a[start:end] = merge_sort(a[start:end])
        size = step
    return a


if __name__ == "__main__":
    data = [5, 2, 8, 1, 9, 3, 7, 4]
    print("bubble:", bubble_sort(data))
    print("quick:", quick_sort(data))
    print("radix:", radix_sort(data))
    print("tim:", timsort(data))