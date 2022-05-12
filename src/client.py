from enum import Enum
from numbers import Number

from src.provider.provider import AbstractProvider
from open_feature import OpenFeatureProvider, OpenFeature


class FlagType(Enum):
    BOOLEAN = 1
    STRING = 2
    NUMBER = 3


class OpenFeatureClient:
    def __init__(self, name: str, version: str, context: Context, hooks: list = []):
        self.name = name
        self.version = version
        self.context = context
        self.hooks = hooks

    def get_boolean_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> bool:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_boolean_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_boolean_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def get_string_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> str:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_string_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_string_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def get_number_value(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ) -> Number:
        return self.evaluate_flag(
            FlagType.BOOLEAN,
            key,
            defaultValue,
            evaluationContext,
            flagEvaluationOptions,
        )

    def get_number_details(
        self, key: str, defaultValue: bool, evaluationContext, flagEvaluationOptions
    ):
        return self.get_number_details(
            key, defaultValue, evaluationContext, flagEvaluationOptions
        )

    def evaluate_flag(
        self,
        flag_type: FlagType,
        key: str,
        defaultValue: bool,
        evaluationContext,
        flagEvaluationOptions,
    ):
        provider = OpenFeature.get_provider()
        if flag_type is FlagType.BOOLEAN:
            return provider.getBooleanEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )
        if flag_type is FlagType.NUMBER:
            return provider.getNumberEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )
        if flag_type is FlagType.STRING:
            return provider.getStringEvaluation(
                key, defaultValue, evaluationContext, flagEvaluationOptions
            )


#   async getBooleanValue(
#     flagKey: string,
#     defaultValue: boolean,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<boolean> {
#     return (
#       await this.getBooleanDetails(flagKey, defaultValue, context, options)
#     ).value;
#   }
#
#   getBooleanDetails(
#     flagKey: string,
#     defaultValue: boolean,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<FlagEvaluationDetails<boolean>> {
#     return this.evaluateFlag(
#       'boolean',
#       flagKey,
#       defaultValue,
#       context,
#       options
#     );
#   }
#
#   async getStringValue(
#     flagKey: string,
#     defaultValue: string,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<string> {
#     return (
#       await this.getStringDetails(flagKey, defaultValue, context, options)
#     ).value;
#   }
#
#   getStringDetails(
#     flagKey: string,
#     defaultValue: string,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<FlagEvaluationDetails<string>> {
#     return this.evaluateFlag('string', flagKey, defaultValue, context, options);
#   }
#
#   async getNumberValue(
#     flagKey: string,
#     defaultValue: number,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<number> {
#     return (
#       await this.getNumberDetails(flagKey, defaultValue, context, options)
#     ).value;
#   }
#
#   getNumberDetails(
#     flagKey: string,
#     defaultValue: number,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<FlagEvaluationDetails<number>> {
#     return this.evaluateFlag('number', flagKey, defaultValue, context, options);
#   }
#
#   async getObjectValue<T extends object>(
#     flagKey: string,
#     defaultValue: T,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<T> {
#     return (
#       await this.getObjectDetails(flagKey, defaultValue, context, options)
#     ).value;
#   }
#
#   getObjectDetails<T extends object>(
#     flagKey: string,
#     defaultValue: T,
#     context?: Context,
#     options?: FlagEvaluationOptions
#   ): Promise<FlagEvaluationDetails<T>> {
#     return this.evaluateFlag('json', flagKey, defaultValue, context, options);
#   }
#
#   private async evaluateFlag<T extends FlagValue>(
#     flagValueType: FlagValueType,
#     flagKey: string,
#     defaultValue: T,
#     context: Context | undefined,
#     options?: FlagEvaluationOptions
#   ): Promise<FlagEvaluationDetails<T>> {
#     const provider = this.getProvider();
#     const flagHooks = options?.hooks ?? [];
#     const allHooks: Hook<FlagValue>[] = [
#       ...OpenFeatureAPI.getInstance().hooks,
#       ...this.hooks,
#       ...flagHooks,
#     ];
#     // merge client context with evaluation context
#     const mergedContext = {
#       ...this.context,
#       ...this.getTransactionContext(),
#       ...context,
#     };
#
#     // this object reference must not change over the course of flag evaluation
#     const hookContext: HookContext = {
#       flagKey,
#       flagValueType,
#       defaultValue,
#       context: mergedContext,
#       client: this,
#       provider,
#       executedHooks: {
#         after: [],
#         before: [],
#         error: [],
#         finally: [],
#       },
#     };
#     let evaluationDetailsPromise: Promise<ProviderEvaluation<FlagValue>>;
#
#     try {
#       this.beforeEvaluation(allHooks, hookContext);
#
#       // if a transformer is defined, run it to prepare the context.
#       const transformedContext =
#         typeof provider.contextTransformer === 'function'
#           ? await provider.contextTransformer(mergedContext)
#           : mergedContext;
#       switch (flagValueType) {
#         case 'boolean': {
#           evaluationDetailsPromise = provider.getBooleanEvaluation(
#             flagKey,
#             defaultValue as boolean,
#             transformedContext,
#             options
#           );
#           break;
#         }
#         case 'string': {
#           evaluationDetailsPromise = provider.getStringEvaluation(
#             flagKey,
#             defaultValue as string,
#             transformedContext,
#             options
#           );
#           break;
#         }
#         case 'number': {
#           evaluationDetailsPromise = provider.getNumberEvaluation(
#             flagKey,
#             defaultValue as number,
#             transformedContext,
#             options
#           );
#           break;
#         }
#         case 'json': {
#           evaluationDetailsPromise = provider.getObjectEvaluation(
#             flagKey,
#             defaultValue as object,
#             transformedContext,
#             options
#           );
#           break;
#         }
#         default: {
#           throw new GeneralError('Unknown flag type');
#         }
#       }
#
#       const evaluationDetails = await evaluationDetailsPromise;
#       return {
#         ...evaluationDetails,
#         value: this.afterEvaluation(
#           allHooks,
#           hookContext,
#           evaluationDetails
#         ) as T,
#         flagKey,
#         executedHooks: hookContext.executedHooks,
#       };
#     } catch (err) {
#       if (this.isError(err)) {
#         this.errorEvaluation(allHooks, hookContext, err);
#       }
#       return {
#         flagKey,
#         executedHooks: hookContext.executedHooks,
#         value: defaultValue,
#         reason: Reason.ERROR,
#       };
#     } finally {
#       this.finallyEvaluation(allHooks, hookContext);
#     }
#   }
#
#   getTransactionContext(): Context {
#     return openfeature.getTransactionContext();
#   }
#
#   private beforeEvaluation(allHooks: Hook[], hookContext: HookContext) {
#     const mergedContext = allHooks.reduce(
#       (accumulated: Context, hook: Hook): Context => {
#         if (typeof hook?.before === 'function') {
#           hookContext.executedHooks.before.push(hook.name);
#           return {
#             ...accumulated,
#             ...hook.before(hookContext),
#           };
#         }
#         return accumulated;
#       },
#       hookContext.context
#     );
#     hookContext.context = mergedContext;
#   }
#
#   private afterEvaluation(
#     allHooks: Hook[],
#     hookContext: HookContext,
#     evaluationDetails: ProviderEvaluation<FlagValue>
#   ): FlagValue {
#     return allHooks.reduce((accumulated: FlagValue, hook) => {
#       if (typeof hook?.after === 'function') {
#         hookContext.executedHooks.after.push(hook.name);
#         return (
#           hook.after(hookContext, {
#             ...evaluationDetails,
#             flagKey: hookContext.flagKey,
#             executedHooks: hookContext.executedHooks,
#           }) ?? accumulated
#         );
#       }
#       return accumulated;
#     }, evaluationDetails.value);
#   }
#
#   private finallyEvaluation(allHooks: Hook[], hookContext: HookContext): void {
#     allHooks.forEach((hook) => {
#       if (typeof hook?.finally === 'function') {
#         hookContext.executedHooks.finally.push(hook.name);
#         return hook.finally(hookContext);
#       }
#     });
#   }
#
#   private errorEvaluation(
#     allHooks: Hook[],
#     hookContext: HookContext,
#     err: Error
#   ): void {
#     // Workaround for error scoping issue
#     const error = err;
#     allHooks.forEach((hook) => {
#       if (typeof hook?.error === 'function') {
#         hookContext.executedHooks.error.push(hook.name);
#         return hook.error(hookContext, error);
#       }
#     });
#   }
#
#   private getAllHooks(options: FlagEvaluationOptions | undefined) {
#     const flagHooks = options?.hooks ?? [];
#     const allHooks: Hook<FlagValue>[] = [
#       ...OpenFeatureAPI.getInstance().hooks,
#       ...this.hooks,
#       ...flagHooks,
#     ];
#     return allHooks;
#   }
#
#   private getProvider(): FeatureProvider<unknown> {
#     return (this.api.getProvider() ??
#       NOOP_FEATURE_PROVIDER) as FeatureProvider<unknown>;
#   }
#
#   private isError(err: unknown): err is Error {
#     return (
#       (err as Error).stack !== undefined && (err as Error).message !== undefined
#     );
#   }
# }
