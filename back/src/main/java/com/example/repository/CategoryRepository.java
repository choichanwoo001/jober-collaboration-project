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

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("update Category c set c.usageCount = c.usageCount + 1 where c.name = :name")
    int incrementUsageCountByName(@Param("name") String name);
}