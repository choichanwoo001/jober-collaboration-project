package com.example.repository;

import com.example.entity.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface CategoryRepository extends JpaRepository<Category, Long> {
    Optional<Category> findByName(String name);
    /**
     * 카테고리 사용량을 DB에서 원자적으로 1 증가시킵니다.
     * 동시 요청 시 lock 점유 시간을 최소화하여 데드락/경합을 줄입니다.
     */
    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update Category c set c.usageCount = c.usageCount + 1 where c.name = :name")

    int incrementUsageCountByName(@Param("name") String name);
}