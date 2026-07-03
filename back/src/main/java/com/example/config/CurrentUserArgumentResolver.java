package com.example.config;

import org.springframework.core.MethodParameter;
import org.springframework.lang.NonNull;
import org.springframework.lang.Nullable;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.authentication.AnonymousAuthenticationToken;
import org.springframework.stereotype.Component;
import org.springframework.web.bind.support.WebDataBinderFactory;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.method.support.HandlerMethodArgumentResolver;
import org.springframework.web.method.support.ModelAndViewContainer;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;
import lombok.RequiredArgsConstructor;
import com.example.service.UserService;
import com.example.common.annotation.CurrentUser;
import com.example.dto.UserDto;
import com.example.entity.Account;

@Component
@RequiredArgsConstructor
public class CurrentUserArgumentResolver implements HandlerMethodArgumentResolver {
    private final UserService userService;

    @Override
    public boolean supportsParameter(@NonNull MethodParameter parameter) {
        return parameter.hasParameterAnnotation(CurrentUser.class)
            && (parameter.getParameterType().equals(UserDto.class)
                || parameter.getParameterType().equals(Account.class));
    }

    @Override
    public Object resolveArgument(@NonNull MethodParameter parameter, @Nullable ModelAndViewContainer mavContainer,
                                  @NonNull NativeWebRequest webRequest, @Nullable WebDataBinderFactory binderFactory) {
        var auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()
            || auth instanceof AnonymousAuthenticationToken) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unauthorized");
        }
        Object principal = auth.getPrincipal();
        if (parameter.getParameterType().equals(UserDto.class)) {
            if (principal instanceof Account acc) return userService.convertToUserDto(acc);
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unsupported principal");
        }
        if (parameter.getParameterType().equals(Account.class)) {
            if (principal instanceof Account acc) return acc;
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unsupported principal");
        }
        throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Unsupported parameter");
    }
}
